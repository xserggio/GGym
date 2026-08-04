"""Weekly volume by pattern and Epley 1RM records (spec §7)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _setup_session(client, ctx) -> str:
    session_id = str(uuid.uuid4())
    client.post(
        "/sync",
        json={
            "sessions": [
                {
                    "id": session_id,
                    "routine_day_id": ctx["routine_day_id"],
                    "started_at": _now(),
                    "status": "completed",
                    "ended_at": _now(),
                }
            ]
        },
    )
    return session_id


def _log(client, ctx, session_id, set_number, weight, reps) -> None:
    client.post(
        "/sync",
        json={
            "set_logs": [
                {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "exercise_id": ctx["exercise_id"],
                    "set_number": set_number,
                    "weight_kg": weight,
                    "reps": reps,
                    "created_at": _now(),
                }
            ]
        },
    )


def test_weekly_volume_counts_effective_sets_by_pattern(client, ctx) -> None:
    sid = _setup_session(client, ctx)
    _log(client, ctx, sid, 1, 80.0, 8)
    _log(client, ctx, sid, 2, 100.0, 5)

    volume = client.get("/me/volume").json()
    by_pattern = {g["pattern"]: g["sets"] for g in volume}
    assert by_pattern.get("empuje_horizontal") == 2  # Press banca


def test_records_use_best_epley_1rm(client, ctx) -> None:
    sid = _setup_session(client, ctx)
    _log(client, ctx, sid, 1, 80.0, 8)  # 1RM = 80 * (1 + 8/30) = 101.3
    _log(client, ctx, sid, 2, 100.0, 5)  # 1RM = 100 * (1 + 5/30) = 116.7 (best)

    records = client.get("/me/records").json()
    press = next(r for r in records if r["exercise_name"] == "Press banca")
    assert press["one_rm"] == 116.7
    assert press["weight_kg"] == 100.0
    assert press["reps"] == 5


def test_history_includes_day_name_and_position(client, ctx) -> None:
    _setup_session(client, ctx)
    history = client.get("/me/history").json()
    assert history
    assert history[0]["position"] == 1
    assert history[0]["day_name"] == "Torso (fuerza)"
