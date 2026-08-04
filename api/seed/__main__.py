"""Seed runner. Idempotent — safe to re-run.

    ../.venv/Scripts/python -m seed             # catalogue + a routine per user
    ../.venv/Scripts/python -m seed --user marta
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.db import SessionLocal
from app.models import (
    Exercise,
    Routine,
    RoutineDay,
    RoutineDayExercise,
    User,
    UserState,
)

from .catalog import CATALOG, default_rest_s
from .routine import ROUTINE_DAYS, ROUTINE_NAME


def seed_catalog(db: OrmSession) -> dict[str, Exercise]:
    """Insert missing exercises (keyed by name). Returns name -> Exercise."""
    existing = {e.name: e for e in db.scalars(select(Exercise)).all()}
    added = 0
    for name, pattern, equipment, description in CATALOG:
        if name in existing:
            continue
        exercise = Exercise(
            name=name,
            pattern=pattern,
            equipment=equipment,
            description=description,
            default_rest_s=default_rest_s(pattern, equipment),
        )
        db.add(exercise)
        existing[name] = exercise
        added += 1
    db.flush()
    print(f"catalogue: {added} added, {len(existing)} total")
    return existing


def seed_routine_for_user(
    db: OrmSession, user: User, catalog: dict[str, Exercise]
) -> None:
    """Create a private copy of the routine for one user (spec D3). Skips users
    that already have a routine."""
    has_routine = db.scalar(
        select(Routine.id).where(Routine.user_id == user.id).limit(1)
    )
    if has_routine is not None:
        print(f"routine: '{user.username}' already has one, skipped")
        return

    routine = Routine(user_id=user.id, name=ROUTINE_NAME, active=True)
    db.add(routine)
    db.flush()

    for day_tpl in ROUTINE_DAYS:
        day = RoutineDay(
            routine_id=routine.id,
            position=day_tpl.position,
            name=day_tpl.name,
            suggested_dow=day_tpl.suggested_dow,
        )
        db.add(day)
        db.flush()
        for order_index, ex in enumerate(day_tpl.exercises):
            exercise = catalog.get(ex.name)
            if exercise is None:
                sys.exit(
                    f"error: routine references unknown exercise '{ex.name}'"
                )
            db.add(
                RoutineDayExercise(
                    routine_day_id=day.id,
                    exercise_id=exercise.id,
                    order_index=order_index,
                    target_sets=ex.target_sets,
                    rep_min=ex.rep_min,
                    rep_max=ex.rep_max,
                    rest_s=None,  # fall back to Exercise.default_rest_s
                )
            )

    # Point the wheel at the first session.
    state = db.get(UserState, user.id)
    if state is None:
        db.add(
            UserState(user_id=user.id, routine_id=routine.id, next_position=1)
        )
    print(f"routine: created for '{user.username}'")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seed", description="Seed catalogue and routine")
    parser.add_argument("--user", help="seed only this username (default: all users)")
    args = parser.parse_args(argv)

    with SessionLocal() as db:
        catalog = seed_catalog(db)

        query = select(User)
        if args.user:
            query = query.where(User.username == args.user)
        users = db.scalars(query).all()

        if not users:
            print("no users to seed a routine for (create one with app.cli)")
        for user in users:
            seed_routine_for_user(db, user, catalog)

        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
