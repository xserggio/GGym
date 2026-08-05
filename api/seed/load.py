"""Load the catalogue and routine from the canonical JSON seed (routine.json).

Exercise ids are stable slugs from the file — never regenerated. Idempotent:
exercises are upserted by id; a user keeps any routine they already have.

    ../.venv/Scripts/python -m seed              # bundled routine.json, all users
    ../.venv/Scripts/python -m seed other.json   # a specific file
    ../.venv/Scripts/python -m seed --user sergio
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

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
from app.models.enums import Equipment, MovementPattern

DEFAULT_JSON = Path(__file__).with_name("routine.json")


def load_data(path: str | Path | None = None) -> dict:
    source = Path(path) if path else DEFAULT_JSON
    return json.loads(source.read_text(encoding="utf-8"))


def load_catalog(db: OrmSession, data: dict) -> int:
    existing = {e.id: e for e in db.scalars(select(Exercise)).all()}
    added = 0
    for item in data["exercises"]:
        fields = {
            "name": item["name"],
            "pattern": MovementPattern(item["pattern"]),
            "equipment": Equipment(item["equipment"]),
            "default_rest_s": item["default_rest_s"],
            "description": item.get("description", ""),
            "per_side": bool(item.get("per_side", False)),
        }
        current = existing.get(item["id"])
        if current is None:
            db.add(Exercise(id=item["id"], media_url=None, **fields))
            added += 1
        else:
            for key, value in fields.items():
                setattr(current, key, value)
    db.flush()
    return added


def load_routine_for_user(db: OrmSession, user: User, data: dict) -> bool:
    if db.scalar(select(Routine.id).where(Routine.user_id == user.id).limit(1)):
        return False
    template = data["routines"][0]
    routine = Routine(user_id=user.id, name=template["name"], active=True)
    db.add(routine)
    db.flush()
    for day_spec in template["days"]:
        day = RoutineDay(
            routine_id=routine.id,
            position=day_spec["position"],
            name=day_spec["name"],
            suggested_dow=day_spec.get("suggested_dow"),
        )
        db.add(day)
        db.flush()
        for order_index, ex in enumerate(day_spec["exercises"]):
            db.add(
                RoutineDayExercise(
                    routine_day_id=day.id,
                    exercise_id=ex["exercise_id"],
                    order_index=order_index,
                    target_sets=ex["sets"],
                    rep_min=ex["rep_min"],
                    rep_max=ex["rep_max"],
                    rest_s=None,
                )
            )
    if db.get(UserState, user.id) is None:
        db.add(UserState(user_id=user.id, routine_id=routine.id, next_position=1))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seed", description="Load the JSON seed")
    parser.add_argument("path", nargs="?", help="JSON file (default: bundled routine.json)")
    parser.add_argument("--user", help="seed a routine only for this username")
    args = parser.parse_args(argv)

    data = load_data(args.path)
    with SessionLocal() as db:
        added = load_catalog(db, data)
        print(f"catalogue: {added} added, {len(data['exercises'])} in file")
        query = select(User)
        if args.user:
            query = query.where(User.username == args.user)
        users = db.scalars(query).all()
        if not users:
            print("no users to seed a routine for (create one with app.cli)")
        for user in users:
            created = load_routine_for_user(db, user, data)
            print(f"routine: {'created' if created else 'skipped'} for '{user.username}'")
        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
