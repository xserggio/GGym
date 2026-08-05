"""Per-exercise weight history (spec pantalla 3)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def _session_with_sets(client, day_id, exercise_id, when, sets) -> None:
    sid = str(uuid.uuid4())
    client.post(
        "/sync",
        json={
            "sessions": [
                {
                    "id": sid,
                    "routine_day_id": day_id,
                    "started_at": when.isoformat(),
                    "status": "completed",
                    "ended_at": when.isoformat(),
                }
            ]
        },
    )
    for number, (weight, reps) in enumerate(sets, start=1):
        client.post(
            "/sync",
            json={
                "set_logs": [
                    {
                        "id": str(uuid.uuid4()),
                        "session_id": sid,
                        "exercise_id": exercise_id,
                        "set_number": number,
                        "weight_kg": weight,
                        "reps": reps,
                        "created_at": when.isoformat(),
                    }
                ]
            },
        )


def test_history_returns_top_set_per_session_chronologically(client, ctx) -> None:
    now = datetime.now(timezone.utc)
    _session_with_sets(
        client, ctx["routine_day_id"], ctx["exercise_id"], now - timedelta(days=2),
        [(60.0, 8), (80.0, 5)],  # top set 80x5
    )
    _session_with_sets(
        client, ctx["routine_day_id"], ctx["exercise_id"], now, [(82.5, 8)]
    )

    history = client.get(f"/me/exercises/{ctx['exercise_id']}/history").json()
    assert len(history) == 2
    assert (history[0]["weight_kg"], history[0]["reps"]) == (80.0, 5)
    assert (history[1]["weight_kg"], history[1]["reps"]) == (82.5, 8)


def test_history_empty_when_never_done(client) -> None:
    assert client.get("/me/exercises/press-banca/history").json() == []
