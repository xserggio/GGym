"""Wheel skip, recovery warning and resume-after-break deload (spec §5.1)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _complete_session(client, day_id, when: datetime) -> str:
    sid = str(uuid.uuid4())
    client.post(
        "/sync",
        json={
            "sessions": [
                {
                    "id": sid,
                    "routine_day_id": day_id,
                    "started_at": _iso(when),
                    "status": "completed",
                    "ended_at": _iso(when),
                }
            ]
        },
    )
    return sid


def test_skip_advances_pointer_without_session(client) -> None:
    assert client.get("/me/state").json()["next_position"] == 1
    assert client.post("/me/skip").json()["next_position"] == 2
    # no completed session was recorded
    assert client.get("/me/history").json() == []


def test_recovery_warning_after_three_consecutive_days(client, ctx) -> None:
    now = datetime.now(timezone.utc)
    for k in range(3):
        _complete_session(client, ctx["routine_day_id"], now - timedelta(days=k))
    assert client.get("/me/today").json()["recovery_warning"] is True


def test_resume_after_break_deloads_suggestion(client, ctx) -> None:
    old = datetime.now(timezone.utc) - timedelta(days=15)
    sid = _complete_session(client, ctx["routine_day_id"], old)
    for n in range(1, 5):
        client.post(
            "/sync",
            json={
                "set_logs": [
                    {
                        "id": str(uuid.uuid4()),
                        "session_id": sid,
                        "exercise_id": ctx["exercise_id"],
                        "set_number": n,
                        "weight_kg": 80.0,
                        "reps": 8,
                        "created_at": _iso(old),
                    }
                ]
            },
        )
    assert client.get("/me/today").json()["resume_after_break"] is True
    sugs = client.get(f"/me/day/{ctx['routine_day_id']}/suggestions").json()
    press = next(s for s in sugs if s["exercise_id"] == ctx["exercise_id"])
    assert press["suggested_weight_kg"] == 72.5  # 80 × 0.9 → nearest 2,5
