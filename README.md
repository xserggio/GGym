# GGym

A strength-training log built for two people who actually use it. Installable
web app (PWA) plus an Android build, backed by a small FastAPI service on a VPS.
The interface is in Spanish.

It is deliberately not a social fitness app: no streaks, no badges, no invented
numbers. If the data does not support a claim, the app says so instead of
guessing — a rule that shaped most of what follows.

## What it does

- **The wheel.** Sessions come round in order rather than being pinned to
  weekdays, so missing a Tuesday does not skip leg day.
- **Progression.** When every set reached the top of its rep range, the next
  session suggests more weight; otherwise it holds.
- **Substitutions.** A busy machine can be swapped for another training the same
  movement pattern, per set, keeping what was already logged.
- **Offline first.** Sets are queued in IndexedDB and synced when the phone gets
  signal back, keyed by UUID so a retry never double-logs.
- **Training phases.** Declare a cut, a lean bulk or maintenance and the app
  measures the *result* against body weight — it never estimates calorie intake,
  because it has no idea what you eat.
- **Routine assistant.** Reads the routine and the logged sets, then proposes
  specific changes: effective weekly sets per muscle counting indirect work, a
  session that does not fit the time available, an exercise substituted so often
  the routine should just say so.

## Layout

```
api/     FastAPI + SQLAlchemy + SQLite (WAL), Alembic migrations, seed data
web/     React + Vite + TypeScript + Tailwind, Dexie offline queue, PWA
web/android/  Capacitor wrapper for the Android build
deploy/  systemd unit, nginx include and a deploy script
docs/    functional spec and design brief
```

## Running it

```bash
# backend
cd api && python -m venv ../.venv && ../.venv/bin/pip install -e .
../.venv/bin/alembic upgrade head
../.venv/bin/python -m app.cli create-user --username you --name You
../.venv/bin/python -m seed --user you
../.venv/bin/uvicorn app.main:app --reload

# frontend
cd web && npm install && npm run dev
```

Tests: `cd api && pytest` and `cd web && npm test`.

Deployment and configuration live in [deploy/README.md](deploy/README.md).
Credentials are never stored in the repo: the deploy script takes the host and
password from the environment, and the push notification keys are generated on
the server.

## Licence

MIT — see [LICENSE](LICENSE).

Exercise photographs come from
[free-exercise-db](https://github.com/yuhonas/free-exercise-db) (public domain)
and are processed to a two-tone treatment at build time. The anatomical outlines
in the recovery map are adapted from
[react-body-highlighter](https://github.com/GV79/react-body-highlighter)
(MIT, © 2020 GV79).
