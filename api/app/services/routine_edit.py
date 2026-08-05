"""Routine editing (spec pantalla 5): edit sets/reps/rest, add/remove/reorder
exercises, reorder sessions. All operations are scoped to the caller's active
routine and re-normalize order indices so they stay 0..N-1 / 1..N."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import Exercise, Routine, RoutineDay, RoutineDayExercise
from ..schemas import ExerciseAdd, ExerciseUpdate


def active_routine_id(db: OrmSession, user_id: str) -> str:
    rid = db.scalar(
        select(Routine.id).where(
            Routine.user_id == user_id, Routine.active.is_(True)
        )
    )
    if rid is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no active routine")
    return rid


def _get_day(db: OrmSession, user_id: str, day_id: str) -> RoutineDay:
    rid = active_routine_id(db, user_id)
    day = db.get(RoutineDay, day_id)
    if day is None or day.routine_id != rid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "session not found")
    return day


def _get_exercise_row(
    db: OrmSession, user_id: str, rde_id: str
) -> RoutineDayExercise:
    rid = active_routine_id(db, user_id)
    row = db.get(RoutineDayExercise, rde_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "exercise not found")
    day = db.get(RoutineDay, row.routine_day_id)
    if day is None or day.routine_id != rid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "exercise not found")
    return row


def update_exercise(
    db: OrmSession, user_id: str, rde_id: str, data: ExerciseUpdate
) -> None:
    row = _get_exercise_row(db, user_id, rde_id)
    row.target_sets = data.target_sets
    row.rep_min = data.rep_min
    row.rep_max = data.rep_max
    row.rest_s = data.rest_s


def add_exercise(
    db: OrmSession, user_id: str, day_id: str, data: ExerciseAdd
) -> None:
    _get_day(db, user_id, day_id)
    if db.get(Exercise, data.exercise_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "exercise not found")
    next_order = (
        db.scalar(
            select(func.count()).select_from(RoutineDayExercise).where(
                RoutineDayExercise.routine_day_id == day_id
            )
        )
        or 0
    )
    db.add(
        RoutineDayExercise(
            routine_day_id=day_id,
            exercise_id=data.exercise_id,
            order_index=next_order,
            target_sets=data.target_sets,
            rep_min=data.rep_min,
            rep_max=data.rep_max,
            rest_s=None,
        )
    )


def remove_exercise(db: OrmSession, user_id: str, rde_id: str) -> None:
    row = _get_exercise_row(db, user_id, rde_id)
    day_id = row.routine_day_id
    db.delete(row)
    db.flush()
    remaining = db.scalars(
        select(RoutineDayExercise)
        .where(RoutineDayExercise.routine_day_id == day_id)
        .order_by(RoutineDayExercise.order_index)
    ).all()
    for i, r in enumerate(remaining):
        r.order_index = i


def reorder_exercises(
    db: OrmSession, user_id: str, day_id: str, ids: list[str]
) -> None:
    _get_day(db, user_id, day_id)
    rows = db.scalars(
        select(RoutineDayExercise).where(
            RoutineDayExercise.routine_day_id == day_id
        )
    ).all()
    if {r.id for r in rows} != set(ids) or len(ids) != len(rows):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "ids must be a permutation of the session's exercises"
        )
    position = {rid: i for i, rid in enumerate(ids)}
    for r in rows:
        r.order_index = position[r.id]


def rename_day(db: OrmSession, user_id: str, day_id: str, name: str) -> None:
    day = _get_day(db, user_id, day_id)
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "name cannot be empty")
    day.name = cleaned[:120]


def reorder_days(db: OrmSession, user_id: str, ids: list[str]) -> None:
    rid = active_routine_id(db, user_id)
    days = db.scalars(
        select(RoutineDay).where(RoutineDay.routine_id == rid)
    ).all()
    if {d.id for d in days} != set(ids) or len(ids) != len(days):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "ids must be a permutation of the sessions"
        )
    position = {did: i + 1 for i, did in enumerate(ids)}
    for d in days:
        d.position = position[d.id]
