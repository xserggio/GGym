"""The `/sync` core (spec §3).

Idempotent by client UUID: re-pushing an event that changes nothing does not
touch the typed tables nor the outbox. `set_logs` are append-only — the only
permitted mutation is a monotonic void=true (spec regla 1). Sessions may change
status/ended_at/notes; the first transition to `completed` advances the wheel
(spec regla 3). Every real change appends one `sync_events` row (the pull log).
"""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..models import (
    BodyWeight,
    Session,
    SetLog,
    SyncEvent,
    TreadmillSession,
    User,
    UserState,
)
from ..models.base import to_naive_utc, utcnow
from ..models.enums import SessionStatus
from ..schemas import (
    BodyWeightIn,
    SessionIn,
    SetLogIn,
    SyncEventOut,
    SyncPush,
    SyncReject,
    SyncResult,
    TreadmillIn,
)
from . import wheel

_PULL_LIMIT = 500


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


# ---------- serializers (server-authoritative payloads for the pull log) ----------
def _session_payload(obj: Session) -> dict:
    return {
        "id": obj.id,
        "routine_day_id": obj.routine_day_id,
        "started_at": _iso(obj.started_at),
        "ended_at": _iso(obj.ended_at),
        "status": obj.status.value,
        "notes": obj.notes,
    }


def _set_log_payload(obj: SetLog) -> dict:
    return {
        "id": obj.id,
        "session_id": obj.session_id,
        "exercise_id": obj.exercise_id,
        "planned_exercise_id": obj.planned_exercise_id,
        "set_number": obj.set_number,
        "weight_kg": float(obj.weight_kg),
        "reps": obj.reps,
        "voided": obj.voided,
        "created_at": _iso(obj.created_at),
    }


def _body_weight_payload(obj: BodyWeight) -> dict:
    return {
        "id": obj.id,
        "measured_on": obj.measured_on.isoformat(),
        "weight_kg": float(obj.weight_kg),
    }


def _treadmill_payload(obj: TreadmillSession) -> dict:
    return {
        "id": obj.id,
        "started_at": _iso(obj.started_at),
        "ended_at": _iso(obj.ended_at),
        "duration_s": obj.duration_s,
    }


def _emit(db: OrmSession, user_id: str, entity: str, entity_id: str, payload: dict) -> None:
    db.add(
        SyncEvent(
            user_id=user_id,
            entity=entity,
            entity_id=entity_id,
            payload=json.dumps(payload),
        )
    )


# ---------- per-entity apply (return True if something changed) ----------
def _apply_session(db: OrmSession, user: User, data: SessionIn) -> bool:
    existing = db.get(Session, data.id)
    started = to_naive_utc(data.started_at)
    ended = to_naive_utc(data.ended_at) if data.ended_at is not None else None

    if existing is None:
        obj = Session(
            id=data.id,
            user_id=user.id,
            routine_day_id=data.routine_day_id,
            started_at=started,
            ended_at=ended,
            status=data.status,
            notes=data.notes,
        )
        db.add(obj)
        if data.status == SessionStatus.completed:
            _advance_wheel(db, user, ended)
        db.flush()
        _emit(db, user.id, "session", obj.id, _session_payload(obj))
        return True

    if existing.user_id != user.id:
        raise PermissionError("session belongs to another user")

    changed = False
    became_completed = (
        data.status == SessionStatus.completed
        and existing.status != SessionStatus.completed
    )
    if existing.status != data.status:
        existing.status = data.status
        changed = True
    if existing.ended_at != ended:
        existing.ended_at = ended
        changed = True
    if existing.notes != data.notes:
        existing.notes = data.notes
        changed = True

    if became_completed:
        _advance_wheel(db, user, ended)
    if changed:
        _emit(db, user.id, "session", existing.id, _session_payload(existing))
    return changed


def _advance_wheel(db: OrmSession, user: User, ended_at: datetime | None) -> None:
    state = db.get(UserState, user.id)
    if state is None:
        return
    total = wheel.total_positions(db, state.routine_id)
    state.next_position = wheel.next_position(state.next_position, total)
    state.last_session_at = ended_at or utcnow()


def _apply_set_log(db: OrmSession, user: User, data: SetLogIn) -> bool:
    session = db.get(Session, data.session_id)
    if session is None or session.user_id != user.id:
        raise ValueError("unknown or unauthorized session")

    existing = db.get(SetLog, data.id)
    if existing is None:
        obj = SetLog(
            id=data.id,
            session_id=data.session_id,
            exercise_id=data.exercise_id,
            planned_exercise_id=data.planned_exercise_id,
            set_number=data.set_number,
            weight_kg=Decimal(str(data.weight_kg)),
            reps=data.reps,
            voided=data.voided,
            created_at=to_naive_utc(data.created_at),
        )
        db.add(obj)
        db.flush()
        _emit(db, user.id, "set_log", obj.id, _set_log_payload(obj))
        return True

    # Append-only: the only permitted mutation is a monotonic void.
    if data.voided and not existing.voided:
        existing.voided = True
        _emit(db, user.id, "set_log", existing.id, _set_log_payload(existing))
        return True
    return False


def _apply_body_weight(db: OrmSession, user: User, data: BodyWeightIn) -> bool:
    existing = db.get(BodyWeight, data.id)
    if existing is None:
        obj = BodyWeight(
            id=data.id,
            user_id=user.id,
            measured_on=data.measured_on,
            weight_kg=Decimal(str(data.weight_kg)),
        )
        db.add(obj)
        db.flush()
        _emit(db, user.id, "body_weight", obj.id, _body_weight_payload(obj))
        return True

    if existing.user_id != user.id:
        raise PermissionError("measurement belongs to another user")
    changed = False
    if float(existing.weight_kg) != data.weight_kg:
        existing.weight_kg = Decimal(str(data.weight_kg))
        changed = True
    if existing.measured_on != data.measured_on:
        existing.measured_on = data.measured_on
        changed = True
    if changed:
        _emit(db, user.id, "body_weight", existing.id, _body_weight_payload(existing))
    return changed


def _apply_treadmill(db: OrmSession, user: User, data: TreadmillIn) -> bool:
    existing = db.get(TreadmillSession, data.id)
    if existing is not None:
        return False
    obj = TreadmillSession(
        id=data.id,
        user_id=user.id,
        started_at=to_naive_utc(data.started_at),
        ended_at=to_naive_utc(data.ended_at) if data.ended_at is not None else None,
        duration_s=data.duration_s,
    )
    db.add(obj)
    db.flush()
    _emit(db, user.id, "treadmill_session", obj.id, _treadmill_payload(obj))
    return True


# ---------- orchestration ----------
def apply_and_pull(db: OrmSession, user: User, push: SyncPush) -> SyncResult:
    accepted = 0
    rejected: list[SyncReject] = []

    # Sessions first: set_logs reference them.
    batches = (
        ("session", push.sessions, _apply_session),
        ("set_log", push.set_logs, _apply_set_log),
        ("body_weight", push.body_weights, _apply_body_weight),
        ("treadmill_session", push.treadmill_sessions, _apply_treadmill),
    )
    for entity, items, apply in batches:
        for data in items:
            try:
                with db.begin_nested():
                    if apply(db, user, data):
                        accepted += 1
            except Exception as exc:  # noqa: BLE001 — reported per event, batch continues
                rejected.append(
                    SyncReject(entity=entity, id=data.id, reason=str(exc))
                )

    db.flush()

    rows = db.scalars(
        select(SyncEvent)
        .where(SyncEvent.user_id == user.id, SyncEvent.seq > push.cursor)
        .order_by(SyncEvent.seq)
        .limit(_PULL_LIMIT)
    ).all()
    events = [
        SyncEventOut(seq=r.seq, entity=r.entity, id=r.entity_id, data=json.loads(r.payload))
        for r in rows
    ]
    new_cursor = rows[-1].seq if rows else push.cursor

    db.commit()
    return SyncResult(
        cursor=new_cursor, accepted=accepted, rejected=rejected, events=events
    )
