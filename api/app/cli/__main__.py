"""User administration CLI (spec §2: no public signup).

    python -m app.cli create-user --username marta --name "Marta"
    python -m app.cli list-users

Password may be passed with --password (non-interactive) or, if omitted, read
twice from a hidden prompt.
"""
from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import select

from ..db import SessionLocal
from ..models import (
    BodyWeight,
    ExercisePreference,
    NotificationSetting,
    PushSubscription,
    Routine,
    RoutineDay,
    RoutineDayExercise,
    Session,
    SetLog,
    SyncEvent,
    TreadmillSession,
    User,
    UserState,
)
from ..security import hash_password
from ..services import routine_profiles


def _read_password() -> str:
    first = getpass.getpass("Password: ")
    if not first:
        sys.exit("error: empty password")
    if first != getpass.getpass("Repeat password: "):
        sys.exit("error: passwords do not match")
    return first


def create_user(args: argparse.Namespace) -> int:
    password = args.password or _read_password()
    with SessionLocal() as db:
        exists = db.scalar(select(User).where(User.username == args.username))
        if exists is not None:
            sys.exit(f"error: username '{args.username}' already exists")
        user = User(
            username=args.username,
            display_name=args.name or args.username,
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()
        print(f"created user '{user.username}' ({user.id})")
    return 0


def list_users(_args: argparse.Namespace) -> int:
    with SessionLocal() as db:
        users = db.scalars(select(User).order_by(User.created_at)).all()
        if not users:
            print("no users")
            return 0
        for user in users:
            print(f"{user.id}  {user.username}  ({user.display_name})")
    return 0


def reset_user(args: argparse.Namespace) -> int:
    """Wipe a user's training data and put their routine back to the seed.

    Destructive and irreversible — back the database up first. Everything the
    user *did* goes (sessions, sets, weigh-ins, treadmill runs, substitution
    preferences, the sync outbox); the read-only `is_original` routine snapshot
    survives and becomes the new active routine, so the account looks freshly
    seeded rather than empty.
    """
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == args.username))
        if user is None:
            sys.exit(f"error: no user '{args.username}'")
        if not args.yes:
            sys.exit("refusing to wipe data without --yes")

        sessions = db.scalars(select(Session).where(Session.user_id == user.id)).all()
        session_ids = [s.id for s in sessions]
        if session_ids:
            for row in db.scalars(
                select(SetLog).where(SetLog.session_id.in_(session_ids))
            ).all():
                db.delete(row)
            db.flush()
        for session in sessions:
            db.delete(session)
        db.flush()

        for model in (
            BodyWeight,
            TreadmillSession,
            ExercisePreference,
            SyncEvent,
            PushSubscription,
            NotificationSetting,
        ):
            for row in db.scalars(select(model).where(model.user_id == user.id)).all():
                db.delete(row)
        db.flush()

        original = routine_profiles.original_for(db, user.id)
        if original is None:
            sys.exit(
                f"error: '{user.username}' has no original snapshot; "
                "run `python -m seed <file> --user <name> --snapshot` first"
            )

        # Build the replacement and move the pointer onto it *before* deleting
        # the old ones: user_state.routine_id is a foreign key, so dropping a
        # routine it still references fails.
        fresh = routine_profiles.copy_routine(db, original, original.name, active=True)
        state = db.get(UserState, user.id)
        if state is None:
            db.add(UserState(user_id=user.id, routine_id=fresh.id, next_position=1))
        else:
            state.routine_id = fresh.id
            state.next_position = 1
            state.last_session_at = None
        db.flush()

        stale = db.scalars(
            select(Routine).where(
                Routine.user_id == user.id,
                Routine.is_original.is_(False),
                Routine.id != fresh.id,
            )
        ).all()
        for routine in stale:
            days = db.scalars(
                select(RoutineDay).where(RoutineDay.routine_id == routine.id)
            ).all()
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
        db.commit()
        print(
            f"reset '{user.username}': {len(sessions)} sessions removed, "
            f"routine restored to '{fresh.name}'"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app.cli", description="User administration")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-user", help="create a user profile")
    create.add_argument("--username", required=True)
    create.add_argument("--name", help="display name (defaults to username)")
    create.add_argument("--password", help="omit for an interactive prompt")
    create.set_defaults(func=create_user)

    listing = sub.add_parser("list-users", help="list existing users")
    listing.set_defaults(func=list_users)

    reset = sub.add_parser(
        "reset-user", help="wipe a user's training data and restore the seeded routine"
    )
    reset.add_argument("--username", required=True)
    reset.add_argument(
        "--yes", action="store_true", help="confirm: this cannot be undone"
    )
    reset.set_defaults(func=reset_user)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
