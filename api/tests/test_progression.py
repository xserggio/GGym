"""Automatic progression suggestions (spec §5.2)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_completed(client, day_id, exercise_id, weight, reps, sets) -> None:
    sid = str(uuid.uuid4())
    client.post(
        "/sync",
        json={
            "sessions": [
                {
                    "id": sid,
                    "routine_day_id": day_id,
                    "started_at": _iso(),
                    "status": "completed",
                    "ended_at": _iso(),
                }
            ]
        },
    )
    for n in range(1, sets + 1):
        client.post(
            "/sync",
            json={
                "set_logs": [
                    {
                        "id": str(uuid.uuid4()),
                        "session_id": sid,
                        "exercise_id": exercise_id,
                        "set_number": n,
                        "weight_kg": weight,
                        "reps": reps,
                        "created_at": _iso(),
                    }
                ]
            },
        )


def _for(client, day_id, exercise_id) -> dict:
    sugs = client.get(f"/me/day/{day_id}/suggestions").json()
    return next(s for s in sugs if s["exercise_id"] == exercise_id)


def test_no_history_has_no_suggestion(client, ctx) -> None:
    s = _for(client, ctx["routine_day_id"], ctx["exercise_id"])
    assert s["last_weight_kg"] is None
    assert s["suggested_weight_kg"] is None


def test_upper_all_at_rep_max_bumps_2_5(client, ctx) -> None:
    # Press banca rep_max is 8; four sets at 80x8 -> +2,5 kg.
    _log_completed(client, ctx["routine_day_id"], ctx["exercise_id"], 80.0, 8, 4)
    s = _for(client, ctx["routine_day_id"], ctx["exercise_id"])
    assert s["last_weight_kg"] == 80.0
    assert s["all_at_rep_max"] is True
    assert s["suggested_weight_kg"] == 82.5


def test_below_rep_max_repeats_weight(client, ctx) -> None:
    _log_completed(client, ctx["routine_day_id"], ctx["exercise_id"], 80.0, 6, 4)
    s = _for(client, ctx["routine_day_id"], ctx["exercise_id"])
    assert s["all_at_rep_max"] is False
    assert s["suggested_weight_kg"] == 80.0


def test_lower_pattern_bumps_5(client) -> None:
    routine = client.get("/me/routine").json()
    day2 = next(d for d in routine["days"] if d["position"] == 2)
    squat = next(e for e in day2["exercises"] if e["exercise"]["id"] == "sentadilla")
    _log_completed(
        client, day2["id"], "sentadilla", 100.0, squat["rep_max"], squat["target_sets"]
    )
    s = _for(client, day2["id"], "sentadilla")
    assert s["all_at_rep_max"] is True
    assert s["suggested_weight_kg"] == 105.0
