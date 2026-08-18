"""Routine profiles: keep several routines and switch between them.

Editing a routine is destructive by nature — a mistapped stepper changes the
plan silently. Profiles make every risky action reversible:

* the seeded routine is kept as a read-only `is_original` snapshot;
* "restore defaults" copies that snapshot instead of mutating anything, and the
  routine you were using stays behind as an ordinary profile;
* switching profiles never deletes, so history (sessions point at routine days)
  survives.

Deletion is the only irreversible operation, so it is refused whenever the
profile is active, is the original, or has sessions referencing it.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import Routine, RoutineDay, RoutineDayExercise, Session, UserState
from ..schemas import RoutineProfileOut


def _owned(db: OrmSession, user_id: str, routine_id: str) -> Routine:
    routine = db.get(Routine, routine_id)
    if routine is None or routine.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "routine not found")
    return routine


def _session_count(db: OrmSession, routine_id: str) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Session)
            .join(RoutineDay, RoutineDay.id == Session.routine_day_id)
            .where(RoutineDay.routine_id == routine_id)
        )
        or 0
    )


def list_profiles(db: OrmSession, user_id: str) -> list[RoutineProfileOut]:
    routines = db.scalars(
        select(Routine)
        .where(Routine.user_id == user_id)
        .order_by(Routine.is_original, Routine.created_at)
    ).all()
    out: list[RoutineProfileOut] = []
    for routine in routines:
        days = (
            db.scalar(
                select(func.count())
                .select_from(RoutineDay)
                .where(RoutineDay.routine_id == routine.id)
            )
            or 0
        )
        sessions = _session_count(db, routine.id)
        out.append(
            RoutineProfileOut(
                id=routine.id,
                name=routine.name,
                active=routine.active,
                is_original=routine.is_original,
                days=days,
                sessions=sessions,
                # Deleting a profile with history would orphan those sessions.
                can_delete=not routine.active
                and not routine.is_original
                and sessions == 0,
            )
        )
    return out


def copy_routine(
    db: OrmSession, source: Routine, name: str, *, active: bool = False
) -> Routine:
    """Deep-copy a routine (days + exercises) under the same user."""
    clone = Routine(user_id=source.user_id, name=name, active=active)
    db.add(clone)
    db.flush()
    days = db.scalars(
        select(RoutineDay)
        .where(RoutineDay.routine_id == source.id)
        .order_by(RoutineDay.position)
    ).all()
    for day in days:
        new_day = RoutineDay(
            routine_id=clone.id,
            position=day.position,
            name=day.name,
            suggested_dow=day.suggested_dow,
        )
        db.add(new_day)
        db.flush()
        rows = db.scalars(
            select(RoutineDayExercise)
            .where(RoutineDayExercise.routine_day_id == day.id)
            .order_by(RoutineDayExercise.order_index)
        ).all()
        for row in rows:
            db.add(
                RoutineDayExercise(
                    routine_day_id=new_day.id,
                    exercise_id=row.exercise_id,
                    order_index=row.order_index,
                    target_sets=row.target_sets,
                    rep_min=row.rep_min,
                    rep_max=row.rep_max,
                    rest_s=row.rest_s,
                    unit=row.unit,
                )
            )
    db.flush()
    return clone


def activate(db: OrmSession, user_id: str, routine_id: str) -> None:
    routine = _owned(db, user_id, routine_id)
    if routine.is_original:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "the original is read-only; restore it into a new profile instead",
        )
    for other in db.scalars(
        select(Routine).where(Routine.user_id == user_id, Routine.active.is_(True))
    ).all():
        other.active = False
    routine.active = True

    state = db.get(UserState, user_id)
    if state is not None:
        state.routine_id = routine.id
        # The new profile may have fewer sessions than the pointer expects.
        total = (
            db.scalar(
                select(func.count())
                .select_from(RoutineDay)
                .where(RoutineDay.routine_id == routine.id)
            )
            or 0
        )
        if total == 0 or state.next_position > total:
            state.next_position = 1
    db.flush()


def duplicate(db: OrmSession, user_id: str, routine_id: str, name: str) -> Routine:
    source = _owned(db, user_id, routine_id)
    return copy_routine(db, source, name.strip() or f"{source.name} (copia)")


def rename(db: OrmSession, user_id: str, routine_id: str, name: str) -> Routine:
    routine = _owned(db, user_id, routine_id)
    if routine.is_original:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "the original is read-only")
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "name cannot be empty")
    routine.name = cleaned[:120]
    db.flush()
    return routine


def delete(db: OrmSession, user_id: str, routine_id: str) -> None:
    routine = _owned(db, user_id, routine_id)
    if routine.active:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "cannot delete the routine in use"
        )
    if routine.is_original:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "cannot delete the original")
    if _session_count(db, routine.id) > 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "this profile has trained sessions; deleting it would lose that history",
        )
    days = db.scalars(
        select(RoutineDay).where(RoutineDay.routine_id == routine.id)
    ).all()
    # No ORM relationships are declared, so SQLAlchemy cannot infer delete
    # ordering: flush each level before the one it points at, or SQLite rejects
    # the parent delete on a foreign key still in place.
    for day in days:
        for row in db.scalars(
            select(RoutineDayExercise).where(
                RoutineDayExercise.routine_day_id == day.id
            )
        ).all():
            db.delete(row)
    db.flush()
    for day in days:
        db.delete(day)
    db.flush()
    db.delete(routine)
    db.flush()


def original_for(db: OrmSession, user_id: str) -> Routine | None:
    return db.scalar(
        select(Routine).where(
            Routine.user_id == user_id, Routine.is_original.is_(True)
        )
    )


def restore_original(db: OrmSession, user_id: str, name: str | None = None) -> Routine:
    """Copy the pristine routine into a new active profile.

    Nothing is overwritten: whatever was active stays as an inactive profile, so
    an accidental restore is itself undoable.
    """
    original = original_for(db, user_id)
    if original is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "no original snapshot for this user (re-run the seed with --snapshot)",
        )
    clone = copy_routine(db, original, (name or original.name).strip()[:120])
    activate(db, user_id, clone.id)
    return clone
