"""Weekly volume and personal records (spec §7).

Volume is *effective sets per muscle pattern* over the last 7 days — the only
real diagnostic of whether the routine is balanced (decision D2). Records use
Epley's 1RM estimate: weight x (1 + reps/30).
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import Exercise, Session, SetLog
from ..models.base import utcnow
from ..schemas import ExerciseHistoryEntry, RecordOut, VolumeGroup

_RECORDS_LIMIT = 12
_HISTORY_LIMIT = 16


def weekly_volume(db: OrmSession, user_id: str) -> list[VolumeGroup]:
    since = utcnow() - timedelta(days=7)
    rows = db.execute(
        select(Exercise.pattern, func.count(SetLog.id))
        .join(Session, Session.id == SetLog.session_id)
        .join(Exercise, Exercise.id == SetLog.exercise_id)
        .where(
            Session.user_id == user_id,
            SetLog.voided.is_(False),
            SetLog.created_at >= since,
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
