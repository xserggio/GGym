"""Load the catalogue and routine from the canonical JSON seed (routine.json).

Exercise ids are stable slugs from the file — never regenerated. Idempotent:
exercises are upserted by id; a user keeps any routine they already have.

    ../.venv/Scripts/python -m seed              # bundled routine.json, all users
    ../.venv/Scripts/python -m seed other.json   # a specific file
    ../.venv/Scripts/python -m seed --user <username>
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
# Execution cues and common errors, keyed by slug and shared by every routine
# file, so a new routine inherits them without duplicating the text.
TECHNIQUE_JSON = Path(__file__).with_name("technique.json")


def load_technique() -> dict[str, dict]:
    if not TECHNIQUE_JSON.exists():
        return {}
    return json.loads(TECHNIQUE_JSON.read_text(encoding="utf-8")).get("exercises", {})


def load_data(path: str | Path | None = None) -> dict:
    source = Path(path) if path else DEFAULT_JSON
    return json.loads(source.read_text(encoding="utf-8"))


def load_catalog(db: OrmSession, data: dict) -> int:
    existing = {e.id: e for e in db.scalars(select(Exercise)).all()}
    technique = load_technique()
    added = 0
    for item in data["exercises"]:
        cues = technique.get(item["id"], {})
        fields = {
            "name": item["name"],
            "pattern": MovementPattern(item["pattern"]),
            "equipment": Equipment(item["equipment"]),
            "default_rest_s": item["default_rest_s"],
            "description": item.get("description", ""),
            "per_side": bool(item.get("per_side", False)),
            "technique": cues.get("technique", []),
            "mistakes": cues.get("mistakes", []),
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


def _build_routine(
    db: OrmSession, user: User, data: dict, *, active: bool, is_original: bool
) -> Routine:
    """Materialise the JSON routine as rows. Shared by the active routine and
    the read-only original snapshot."""
    template = data["routines"][0]
    routine = Routine(
        user_id=user.id,
        name=template["name"],
        active=active,
        is_original=is_original,
    )
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
                    unit=ex.get("unit", "reps"),
                )
            )
    db.flush()
    return routine


def ensure_original_snapshot(db: OrmSession, user: User, data: dict) -> bool:
    """Create the untouched copy that "restore defaults" copies from.

    Idempotent, and independent of whatever the user has since edited — the
    snapshot comes from the JSON, not from their current routine.
    """
    existing = db.scalar(
        select(Routine).where(
            Routine.user_id == user.id, Routine.is_original.is_(True)
        )
    )
    if existing is not None:
        return False
    _build_routine(db, user, data, active=False, is_original=True)
    return True


def load_routine_for_user(
    db: OrmSession, user: User, data: dict, replace: bool = False
) -> bool:
    existing = db.scalars(
        select(Routine).where(Routine.user_id == user.id, Routine.active.is_(True))
    ).all()
    if existing and not replace:
        return False
    # Deactivate (never delete) the old routine so past sessions that reference
    # its days keep working; the new routine becomes the active one.
    for old in existing:
        old.active = False
    db.flush()

    routine = _build_routine(db, user, data, active=True, is_original=False)
    # Keep a pristine copy so the user can always get back to this plan.
    ensure_original_snapshot(db, user, data)

    # Point the user's state at the new routine.
    state = db.get(UserState, user.id)
    if state is None:
        db.add(UserState(user_id=user.id, routine_id=routine.id, next_position=1))
    else:
        state.routine_id = routine.id
        state.next_position = 1
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seed", description="Load the JSON seed")
    parser.add_argument("path", nargs="?", help="JSON file (default: bundled routine.json)")
    parser.add_argument("--user", help="seed a routine only for this username")
    parser.add_argument(
        "--replace", action="store_true", help="replace the user's existing routine"
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="only create the read-only 'original' copy, leaving the routine in use alone",
    )
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
            if args.snapshot:
                made = ensure_original_snapshot(db, user, data)
                print(
                    f"original: {'created' if made else 'already present'}"
                    f" for '{user.username}'"
                )
                continue
            created = load_routine_for_user(db, user, data, replace=args.replace)
            print(f"routine: {'created' if created else 'skipped'} for '{user.username}'")
        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
