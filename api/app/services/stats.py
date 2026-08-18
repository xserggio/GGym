"""Weekly volume and personal records (spec §7).

Volume is *effective sets per muscle pattern* over the last 7 days — the only
real diagnostic of whether the routine is balanced (decision D2). Records use
Epley's 1RM estimate: weight x (1 + reps/30).
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import Exercise, Session, SetLog, TreadmillSession
from ..models.base import utcnow
from ..models.enums import SessionStatus
from ..schemas import ExerciseHistoryEntry, Milestone, RecordOut, VolumeGroup

_RECORDS_LIMIT = 12
_HISTORY_LIMIT = 16


def weekly_volume(
    db: OrmSession, user_id: str, days: int | None = 7
) -> list[VolumeGroup]:
    """Effective sets per pattern. `days=None` means all time."""
    since = utcnow() - timedelta(days=days) if days is not None else None
    rows = db.execute(
        select(Exercise.pattern, func.count(SetLog.id))
        .join(Session, Session.id == SetLog.session_id)
        .join(Exercise, Exercise.id == SetLog.exercise_id)
        .where(
            Session.user_id == user_id,
            SetLog.voided.is_(False),
            *([SetLog.created_at >= since] if since is not None else []),
        )
        .group_by(Exercise.pattern)
    ).all()
    groups = [VolumeGroup(pattern=pattern, sets=count) for pattern, count in rows]
    return sorted(groups, key=lambda g: g.sets, reverse=True)


def epley_1rm(weight_kg: float, reps: int) -> float:
    return weight_kg * (1 + reps / 30)


def exercise_history(
    db: OrmSession, user_id: str, exercise_id: str
) -> list[ExerciseHistoryEntry]:
    """Top set (heaviest, then most reps) of the exercise per past session,
    oldest first, capped at the last _HISTORY_LIMIT sessions."""
    rows = db.execute(
        select(
            SetLog.session_id,
            Session.started_at,
            SetLog.weight_kg,
            SetLog.reps,
        )
        .join(Session, Session.id == SetLog.session_id)
        .where(
            Session.user_id == user_id,
            SetLog.exercise_id == exercise_id,
            SetLog.voided.is_(False),
        )
    ).all()

    best: dict[str, tuple] = {}
    for session_id, started_at, weight, reps in rows:
        w = float(weight)
        current = best.get(session_id)
        if current is None or (w, reps) > (current[1], current[2]):
            best[session_id] = (started_at, w, reps)

    ordered = sorted(best.values(), key=lambda x: x[0])[-_HISTORY_LIMIT:]
    return [
        ExerciseHistoryEntry(session_on=started.date(), weight_kg=w, reps=reps)
        for started, w, reps in ordered
    ]


def milestones(db: OrmSession, user_id: str) -> list[Milestone]:
    """All-time bests that a per-exercise 1RM table cannot express: the heaviest
    single set, the longest and heaviest sessions, the longest treadmill run.

    `kind` is a key the UI translates; the service never returns display text.
    """
    out: list[Milestone] = []

    heaviest = db.execute(
        select(SetLog.weight_kg, SetLog.reps, Exercise.name, SetLog.created_at)
        .join(Session, Session.id == SetLog.session_id)
        .join(Exercise, Exercise.id == SetLog.exercise_id)
        .where(Session.user_id == user_id, SetLog.voided.is_(False))
        .order_by(SetLog.weight_kg.desc())
        .limit(1)
    ).first()
    if heaviest is not None:
        weight, reps, name, created = heaviest
        out.append(
            Milestone(
                kind="heaviest_set",
                value=float(weight),
                unit="kg",
                detail=f"{name} · {reps} reps",
                achieved_on=created.date(),
            )
        )

    sessions = db.scalars(
        select(Session).where(
            Session.user_id == user_id,
            Session.status == SessionStatus.completed,
            Session.ended_at.is_not(None),
        )
    ).all()
    if sessions:
        longest = max(sessions, key=lambda s: (s.ended_at - s.started_at))
        out.append(
            Milestone(
                kind="longest_session",
                value=round((longest.ended_at - longest.started_at).total_seconds() / 60),
                unit="min",
                detail=None,
                achieved_on=longest.ended_at.date(),
            )
        )

        volumes = db.execute(
            select(
                SetLog.session_id,
                func.sum(SetLog.weight_kg * SetLog.reps),
            )
            .where(
                SetLog.session_id.in_([s.id for s in sessions]),
                SetLog.voided.is_(False),
            )
            .group_by(SetLog.session_id)
        ).all()
        if volumes:
            session_id, volume = max(volumes, key=lambda row: row[1] or 0)
            when = next((s.ended_at for s in sessions if s.id == session_id), None)
            out.append(
                Milestone(
                    kind="best_session_volume",
                    value=round(float(volume or 0)),
                    unit="kg",
                    detail=None,
                    achieved_on=when.date() if when else None,
                )
            )

    run = db.scalar(
        select(TreadmillSession)
        .where(TreadmillSession.user_id == user_id)
        .order_by(TreadmillSession.duration_s.desc())
        .limit(1)
    )
    if run is not None:
        out.append(
            Milestone(
                kind="longest_run",
                value=round(run.duration_s / 60),
                unit="min",
                detail=None,
                achieved_on=run.started_at.date(),
            )
        )
    return out


def records(db: OrmSession, user_id: str) -> list[RecordOut]:
    rows = db.execute(
        select(
            SetLog.exercise_id,
            Exercise.name,
            SetLog.weight_kg,
            SetLog.reps,
            SetLog.created_at,
        )
        .join(Session, Session.id == SetLog.session_id)
        .join(Exercise, Exercise.id == SetLog.exercise_id)
        .where(Session.user_id == user_id, SetLog.voided.is_(False))
    ).all()

    best: dict[str, RecordOut] = {}
    for exercise_id, name, weight, reps, created in rows:
        one_rm = epley_1rm(float(weight), reps)
        current = best.get(exercise_id)
        if current is None or one_rm > current.one_rm:
            best[exercise_id] = RecordOut(
                exercise_id=exercise_id,
                exercise_name=name,
                weight_kg=float(weight),
                reps=reps,
                one_rm=round(one_rm, 1),
                achieved_on=created.date(),
            )
    return sorted(best.values(), key=lambda r: r.one_rm, reverse=True)[:_RECORDS_LIMIT]
