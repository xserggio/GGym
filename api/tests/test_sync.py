"""/sync idempotency, append-only voiding, and wheel advance on completion."""
from __future__ import annotations

import uuid


def _iso() -> str:
    return "2026-08-04T18:00:00"


def test_sync_is_idempotent_and_advances_wheel(client, ctx) -> None:
    session_id = str(uuid.uuid4())
    set_id = str(uuid.uuid4())

    push = {
        "cursor": 0,
        "sessions": [
            {
                "id": session_id,
                "routine_day_id": ctx["routine_day_id"],
                "started_at": _iso(),
                "status": "in_progress",
            }
        ],
        "set_logs": [
            {
                "id": set_id,
                "session_id": session_id,
                "exercise_id": ctx["exercise_id"],
                "set_number": 1,
                "weight_kg": 80.0,
                "reps": 8,
                "created_at": _iso(),
            }
        ],
    }

    # First push: session + set_log accepted, two events pulled back.
    r1 = client.post("/sync", json=push).json()
    assert r1["accepted"] == 2
    assert {e["entity"] for e in r1["events"]} == {"session", "set_log"}
    cursor = r1["cursor"]
    assert cursor > 0

    # Re-push identical batch: nothing changes, no new events after cursor.
    r2 = client.post("/sync", json={**push, "cursor": cursor}).json()
    assert r2["accepted"] == 0
    assert r2["events"] == []
    assert r2["cursor"] == cursor

    # Wheel has not moved yet (session still in progress).
    assert client.get("/me/state").json()["next_position"] == 1

    # Complete the session -> wheel advances exactly once.
    complete = {
        "cursor": cursor,
        "sessions": [
            {
                "id": session_id,
                "routine_day_id": ctx["routine_day_id"],
                "started_at": _iso(),
                "ended_at": _iso(),
                "status": "completed",
            }
        ],
    }
    r3 = client.post("/sync", json=complete).json()
    assert r3["accepted"] == 1
    assert client.get("/me/state").json()["next_position"] == 2

    # Re-completing is a no-op: the wheel does not advance twice.
    r4 = client.post("/sync", json={**complete, "cursor": r3["cursor"]}).json()
    assert r4["accepted"] == 0
    assert client.get("/me/state").json()["next_position"] == 2

    # Void the set: accepted once, then idempotent.
    void = {
        "cursor": r3["cursor"],
        "set_logs": [
            {
                "id": set_id,
                "session_id": session_id,
                "exercise_id": ctx["exercise_id"],
                "set_number": 1,
                "weight_kg": 80.0,
                "reps": 8,
                "voided": True,
                "created_at": _iso(),
            }
        ],
    }
    assert client.post("/sync", json=void).json()["accepted"] == 1
    assert client.post("/sync", json=void).json()["accepted"] == 0


def test_set_log_for_unknown_session_is_rejected(client, ctx) -> None:
    push = {
        "set_logs": [
            {
                "id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),  # does not exist
                "exercise_id": ctx["exercise_id"],
                "set_number": 1,
                "weight_kg": 60.0,
                "reps": 10,
                "created_at": _iso(),
            }
        ]
    }
    result = client.post("/sync", json=push).json()
    assert result["accepted"] == 0
    assert len(result["rejected"]) == 1
    assert result["rejected"][0]["entity"] == "set_log"
