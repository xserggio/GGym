"""The wheel (spec §5.1) and routine read helpers.

The pointer `user_state.next_position` advances only when a session is completed
(or explicitly skipped), never by date. Wrapping is 1..N -> 1.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import (
    Exercise,
    Routine,
    RoutineDay,
    RoutineDayExercise,
    UserState,
)
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
