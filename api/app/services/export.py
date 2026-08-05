"""Export all of a user's data to a plain JSON dict (spec §6, §7.3): data
ownership, independent of the server backup."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..models import (
    BodyWeight,
    ExercisePreference,
    Session,
    SetLog,
    TreadmillSession,
    User,
    UserState,
)
from ..models.base import utcnow


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def export_all(db: OrmSession, user: User) -> dict:
    state = db.get(UserState, user.id)
    sessions = db.scalars(
        select(Session).where(Session.user_id == user.id).order_by(Session.started_at)
    ).all()
    set_logs = db.scalars(
        select(SetLog)
        .join(Session, Session.id == SetLog.session_id)
        .where(Session.user_id == user.id)
        .order_by(SetLog.created_at)
    ).all()
    weights = db.scalars(
        select(BodyWeight)
        .where(BodyWeight.user_id == user.id)
        .order_by(BodyWeight.measured_on)
    ).all()
    treadmill = db.scalars(
        select(TreadmillSession)
        .where(TreadmillSession.user_id == user.id)
        .order_by(TreadmillSession.started_at)
    ).all()
    prefs = db.scalars(
        select(ExercisePreference).where(ExercisePreference.user_id == user.id)
    ).all()

    return {
        "exported_at": _iso(utcnow()),
        "profile": {"username": user.username, "display_name": user.display_name},
        "state": (
            {
                "next_position": state.next_position,
                "last_session_at": _iso(state.last_session_at),
            }
            if state
            else None
        ),
        "sessions": [
            {
                "id": s.id,
                "routine_day_id": s.routine_day_id,
                "started_at": _iso(s.started_at),
                "ended_at": _iso(s.ended_at),
                "status": s.status.value,
                "notes": s.notes,
            }
            for s in sessions
        ],
        "set_logs": [
            {
                "id": x.id,
                "session_id": x.session_id,
                "exercise_id": x.exercise_id,
                "planned_exercise_id": x.planned_exercise_id,
                "set_number": x.set_number,
                "weight_kg": float(x.weight_kg),
                "reps": x.reps,
                "voided": x.voided,
                "created_at": _iso(x.created_at),
            }
            for x in set_logs
        ],
        "body_weights": [
            {
                "id": b.id,
                "measured_on": b.measured_on.isoformat(),
                "weight_kg": float(b.weight_kg),
            }
            for b in weights
        ],
        "treadmill_sessions": [
            {
                "id": t.id,
                "started_at": _iso(t.started_at),
                "ended_at": _iso(t.ended_at),
                "duration_s": t.duration_s,
            }
            for t in treadmill
        ],
        "exercise_preferences": [
            {
                "planned_exercise_id": p.planned_exercise_id,
                "preferred_exercise_id": p.preferred_exercise_id,
                "substitution_count": p.substitution_count,
            }
            for p in prefs
        ],
    }
