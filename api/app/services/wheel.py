"""The wheel (spec §5.1) and routine read helpers.

The pointer `user_state.next_position` advances only when a session is completed
(or explicitly skipped), never by date. Wrapping is 1..N -> 1.
"""
from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import (
    Exercise,
    Routine,
    RoutineDay,
    RoutineDayExercise,
    Session,
    UserState,
)
from ..models.base import utcnow
from ..models.enums import SessionStatus

RESUME_BREAK_DAYS = 10
RECOVERY_STREAK_DAYS = 3
from ..schemas import (
    ExerciseSummary,
    RoutineDayExerciseOut,
    RoutineDayOut,
    RoutineOut,
)


def get_active_routine(db: OrmSession, user_id: str) -> Routine:
    routine = db.scalar(
        select(Routine).where(Routine.user_id == user_id, Routine.active.is_(True))
    )
    if routine is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no active routine")
    return routine


def total_positions(db: OrmSession, routine_id: str) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(RoutineDay).where(
                RoutineDay.routine_id == routine_id
            )
        )
        or 0
    )


def next_position(current: int, total: int) -> int:
    """Advance the wheel, wrapping the last position back to the first."""
    if total <= 0:
        return current
    return (current % total) + 1


def get_state(db: OrmSession, user_id: str) -> UserState:
    state = db.get(UserState, user_id)
    if state is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user has no state (seed first)")
    return state


def skip(db: OrmSession, user_id: str) -> UserState:
    """Advance the pointer without recording a session (spec §5.1). Does not
    touch last_session_at — nothing was trained."""
    state = get_state(db, user_id)
    state.next_position = next_position(
        state.next_position, total_positions(db, state.routine_id)
    )
    return state


def recovery_warning(db: OrmSession, user_id: str) -> bool:
    """True when there are completed sessions on RECOVERY_STREAK_DAYS consecutive
    calendar days ending today or yesterday (spec §5.1, non-blocking)."""
    since = utcnow() - timedelta(days=RECOVERY_STREAK_DAYS + 2)
    ended = db.scalars(
        select(Session.ended_at).where(
            Session.user_id == user_id,
            Session.status == SessionStatus.completed,
            Session.ended_at.is_not(None),
            Session.ended_at >= since,
        )
    ).all()
    days = sorted({e.date() for e in ended}, reverse=True)
    if len(days) < RECOVERY_STREAK_DAYS:
        return False
    streak = 1
    for prev, cur in zip(days, days[1:]):
        if cur == prev - timedelta(days=1):
            streak += 1
        else:
            break
    today = utcnow().date()
    return streak >= RECOVERY_STREAK_DAYS and days[0] >= today - timedelta(days=1)


def resume_after_break(db: OrmSession, user_id: str) -> bool:
    """True when it's been more than RESUME_BREAK_DAYS since the last session
    (spec §5.1): weights are suggested at −10%."""
    state = db.get(UserState, user_id)
    if state is None or state.last_session_at is None:
        return False
    return (utcnow() - state.last_session_at).days > RESUME_BREAK_DAYS


def _day_out(db: OrmSession, day: RoutineDay) -> RoutineDayOut:
    rows = db.execute(
        select(RoutineDayExercise, Exercise)
        .join(Exercise, Exercise.id == RoutineDayExercise.exercise_id)
        .where(RoutineDayExercise.routine_day_id == day.id)
        .order_by(RoutineDayExercise.order_index)
    ).all()
    exercises = [
        RoutineDayExerciseOut(
            id=rde.id,
            order_index=rde.order_index,
            target_sets=rde.target_sets,
            rep_min=rde.rep_min,
            rep_max=rde.rep_max,
            rest_s=rde.rest_s if rde.rest_s is not None else ex.default_rest_s,
            unit=rde.unit,
            exercise=ExerciseSummary.model_validate(ex),
        )
        for rde, ex in rows
    ]
    return RoutineDayOut(
        id=day.id,
        position=day.position,
        name=day.name,
        suggested_dow=day.suggested_dow,
        exercises=exercises,
    )


def routine_out(db: OrmSession, routine: Routine) -> RoutineOut:
    days = db.scalars(
        select(RoutineDay)
        .where(RoutineDay.routine_id == routine.id)
        .order_by(RoutineDay.position)
    ).all()
    return RoutineOut(
        id=routine.id,
        name=routine.name,
        active=routine.active,
        days=[_day_out(db, d) for d in days],
    )


def current_day_out(db: OrmSession, user_id: str) -> RoutineDayOut:
    state = get_state(db, user_id)
    day = db.scalar(
        select(RoutineDay).where(
            RoutineDay.routine_id == state.routine_id,
            RoutineDay.position == state.next_position,
        )
    )
    if day is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no routine day at pointer")
    return _day_out(db, day)
