"""Test fixtures: an isolated SQLite DB, seeded catalogue + routine, and a
logged-in TestClient. Environment is set before importing the app so the engine
binds to the throwaway database."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.gettempdir()) / "gym_test.db"
for suffix in ("", "-wal", "-shm"):
    p = Path(str(_TMP) + suffix)
    if p.exists():
        p.unlink()

os.environ["GYM_DATABASE_URL"] = f"sqlite:///{_TMP.as_posix()}"
os.environ["GYM_JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Exercise, RoutineDay, User  # noqa: E402
from app.security import hash_password  # noqa: E402
from seed.load import load_catalog, load_data, load_routine_for_user  # noqa: E402

TEST_PASSWORD = "pw-test"


@pytest.fixture(autouse=True)
def _schema() -> None:
    # Fresh schema + seed per test: the sync outbox accumulates, so tests must
    # not share a database or their event/cursor assertions leak into each other.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        user = User(
            username="tester",
            display_name="Tester",
            password_hash=hash_password(TEST_PASSWORD),
        )
        db.add(user)
        db.flush()
        data = load_data()
        load_catalog(db, data)
        load_routine_for_user(db, user, data)
        db.commit()


@pytest.fixture()
def ctx() -> dict:
    from sqlalchemy import select

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "tester"))
        day = db.scalar(select(RoutineDay).where(RoutineDay.position == 1))
        exercise = db.scalar(select(Exercise).where(Exercise.name == "Press banca"))
        return {
            "user_id": user.id,
            "routine_day_id": day.id,
            "exercise_id": exercise.id,
        }


@pytest.fixture()
def client() -> TestClient:
    c = TestClient(app)
    resp = c.post(
        "/auth/login", json={"username": "tester", "password": TEST_PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return c
