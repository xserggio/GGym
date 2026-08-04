# gym-api

Backend for the strength-training log. FastAPI lands in phase 3; phase 1 is the
schema, migrations and the user-administration CLI.

## Setup

From the repo root (`venv` lives at `../.venv`):

```bash
py -m venv .venv
./.venv/Scripts/python -m pip install -e ./api          # or: sqlalchemy alembic argon2-cffi
```

## Database

SQLite in WAL mode at `api/data/gym.db` (git-ignored). Override with the
`DATABASE_URL` environment variable.

```bash
cd api
../.venv/Scripts/alembic upgrade head     # create / migrate schema
../.venv/Scripts/alembic downgrade base   # drop everything
```

## Users (no public signup — spec §2)

```bash
cd api
../.venv/Scripts/python -m app.cli create-user --username marta --name "Marta"
../.venv/Scripts/python -m app.cli list-users
```

Omit `--password` for a hidden interactive prompt. Passwords are hashed with
Argon2id.

## Layout

```
app/
  config.py     DATABASE_URL resolution
  db.py         engine + session factory (WAL, foreign keys)
  security.py   Argon2 hashing
  models/       SQLAlchemy 2.0 models (spec §4)
  cli/          user administration
migrations/     Alembic
```
