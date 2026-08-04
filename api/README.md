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

## Run the API

```bash
cd api
GYM_JWT_SECRET="<32+ byte secret>" ../.venv/Scripts/python -m uvicorn app.main:app --reload
```

Config is via `GYM_`-prefixed env vars (see `app/config.py`): `GYM_DATABASE_URL`,
`GYM_JWT_SECRET` (use ≥32 bytes in production), `GYM_COOKIE_SECURE=true` behind
HTTPS, `GYM_CORS_ORIGINS`. Interactive docs at `/docs`, OpenAPI at `/openapi.json`
(the frontend types are generated from it).

Auth is a JWT in an httpOnly cookie: `POST /auth/login`, `POST /auth/logout`,
`GET /auth/me`. Reads: `/me/state`, `/me/routine`, `/me/today`, `/me/history`,
`/exercises`. Writes from an active session go through `POST /sync`.

## Tests

```bash
cd api
../.venv/Scripts/python -m pytest -q
```

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
