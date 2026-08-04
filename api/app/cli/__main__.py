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
from ..models import User
from ..security import hash_password


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

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
