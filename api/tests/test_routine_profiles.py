"""Routine profiles exist so editing is never a one-way door: restoring or
switching must not destroy the plan you had, nor the history behind it."""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Routine, RoutineDay, RoutineDayExercise, Session, UserState
from app.models.enums import SessionStatus


def _profiles(client: TestClient) -> list[dict]:
    resp = client.get("/me/routine/profiles")
    assert resp.status_code == 200, resp.text
    return resp.json()


def _active(client: TestClient) -> dict:
    return next(p for p in _profiles(client) if p["active"])


def _first_exercise(client: TestClient) -> dict:
    return client.get("/me/routine").json()["days"][0]["exercises"][0]


def _set_target_sets(client: TestClient, value: int) -> None:
    """ExerciseUpdate is a full replace, so echo the current values back."""
    row = _first_exercise(client)
    resp = client.patch(
        f"/me/routine/exercises/{row['id']}",
        json={
            "target_sets": value,
            "rep_min": row["rep_min"],
            "rep_max": row["rep_max"],
            "rest_s": row["rest_s"],
        },
    )
    assert resp.status_code == 200, resp.text


def test_seed_creates_a_protected_original(client: TestClient) -> None:
    profiles = _profiles(client)
    assert len(profiles) == 2
    original = next(p for p in profiles if p["is_original"])
    assert original["active"] is False
    assert original["can_delete"] is False


def test_restore_brings_back_the_seeded_plan(client: TestClient, ctx: dict) -> None:
    # Wreck the active routine the way a mistap would.
    routine = _active(client)
    seeded_sets = _first_exercise(client)["target_sets"]
    _set_target_sets(client, 99)
    assert _first_exercise(client)["target_sets"] == 99

    resp = client.post("/me/routine/profiles/restore")
    assert resp.status_code == 200, resp.text

    # The restored routine matches the seed again...
    assert _first_exercise(client)["target_sets"] == seeded_sets
    # ...and the wrecked one is still there as a profile, not deleted.
    assert routine["id"] in [p["id"] for p in _profiles(client)]


def test_restore_is_itself_undoable(client: TestClient) -> None:
    before = _active(client)["id"]
    client.post("/me/routine/profiles/restore")
    assert _active(client)["id"] != before
    resp = client.post(f"/me/routine/profiles/{before}/activate")
    assert resp.status_code == 200, resp.text
    assert _active(client)["id"] == before


def test_duplicate_is_an_independent_copy(client: TestClient) -> None:
    source = _active(client)["id"]
    resp = client.post(
        f"/me/routine/profiles/{source}/duplicate", json={"name": "prueba volumen"}
    )
    assert resp.status_code == 200, resp.text
    copy = next(p for p in resp.json() if p["name"] == "prueba volumen")
    source_days = next(p for p in resp.json() if p["id"] == source)["days"]
    assert copy["active"] is False
    assert copy["days"] == source_days

    client.post(f"/me/routine/profiles/{copy['id']}/activate")
    original_sets = _first_exercise(client)["target_sets"]
    _set_target_sets(client, original_sets + 3)

    # Editing the copy leaves the source profile untouched.
    client.post(f"/me/routine/profiles/{source}/activate")
    assert _first_exercise(client)["target_sets"] == original_sets


def test_cannot_delete_the_original_or_the_one_in_use(client: TestClient) -> None:
    profiles = _profiles(client)
    original = next(p for p in profiles if p["is_original"])
    active = next(p for p in profiles if p["active"])
    assert client.delete(f"/me/routine/profiles/{original['id']}").status_code == 400
    assert client.delete(f"/me/routine/profiles/{active['id']}").status_code == 400


def test_cannot_activate_the_original_directly(client: TestClient) -> None:
    original = next(p for p in _profiles(client) if p["is_original"])
    resp = client.post(f"/me/routine/profiles/{original['id']}/activate")
    assert resp.status_code == 400


def test_delete_refuses_to_orphan_history(client: TestClient, ctx: dict) -> None:
    """A profile you have actually trained holds the sessions' day rows."""
    source = _active(client)["id"]
    client.post(f"/me/routine/profiles/{source}/duplicate", json={"name": "con historia"})
    copy = next(p for p in _profiles(client) if p["name"] == "con historia")

    with SessionLocal() as db:
        day = db.scalar(select(RoutineDay).where(RoutineDay.routine_id == copy["id"]))
        db.add(
            Session(
                user_id=ctx["user_id"],
                routine_day_id=day.id,
                status=SessionStatus.completed,
            )
        )
        db.commit()

    assert client.delete(f"/me/routine/profiles/{copy['id']}").status_code == 400
    assert next(p for p in _profiles(client) if p["id"] == copy["id"])["can_delete"] is False


def test_delete_removes_an_unused_profile_and_its_rows(client: TestClient) -> None:
    source = _active(client)["id"]
    client.post(f"/me/routine/profiles/{source}/duplicate", json={"name": "descartable"})
    copy = next(p for p in _profiles(client) if p["name"] == "descartable")
    assert copy["can_delete"] is True

    assert client.delete(f"/me/routine/profiles/{copy['id']}").status_code == 200
    assert all(p["id"] != copy["id"] for p in _profiles(client))
    with SessionLocal() as db:
        assert db.get(Routine, copy["id"]) is None
        assert (
            db.scalars(
                select(RoutineDay).where(RoutineDay.routine_id == copy["id"])
            ).all()
            == []
        )


def test_switching_clamps_a_pointer_past_the_end(client: TestClient, ctx: dict) -> None:
    """A shorter profile must not leave the wheel pointing at nothing."""
    source = _active(client)["id"]
    client.post(f"/me/routine/profiles/{source}/duplicate", json={"name": "corta"})
    copy = next(p for p in _profiles(client) if p["name"] == "corta")

    with SessionLocal() as db:
        # Drop every day but the first, then park the pointer past the end.
        days = db.scalars(
            select(RoutineDay)
            .where(RoutineDay.routine_id == copy["id"])
            .order_by(RoutineDay.position)
        ).all()
        for day in days[1:]:
            for row in db.scalars(
                select(RoutineDayExercise).where(
                    RoutineDayExercise.routine_day_id == day.id
                )
            ).all():
                db.delete(row)
        db.flush()
        for day in days[1:]:
            db.delete(day)
        db.flush()
        db.get(UserState, ctx["user_id"]).next_position = 4
        db.commit()

    client.post(f"/me/routine/profiles/{copy['id']}/activate")
    assert client.get("/me/state").json()["next_position"] == 1
    assert client.get("/me/today").status_code == 200


def test_rename_a_profile(client: TestClient) -> None:
    active = _active(client)["id"]
    resp = client.patch(f"/me/routine/profiles/{active}", json={"name": "mi rutina"})
    assert resp.status_code == 200, resp.text
    assert _active(client)["name"] == "mi rutina"
