"""Alternatives by pattern and substitution counting (spec §5.3)."""
from __future__ import annotations

import uuid


def _iso() -> str:
    return "2026-08-04T18:00:00"


def test_alternatives_share_pattern_and_exclude_self(client, ctx) -> None:
    resp = client.get(f"/exercises/{ctx['exercise_id']}/alternatives")
    assert resp.status_code == 200
    alts = resp.json()
    assert alts, "Press banca should have same-pattern alternatives"
    assert ctx["exercise_id"] not in {a["id"] for a in alts}
    assert all(a["pattern"] == "empuje_horizontal" for a in alts)


def test_substitution_counted_once_per_session(client, ctx) -> None:
    preferred = client.get(f"/exercises/{ctx['exercise_id']}/alternatives").json()[0]["id"]
    session_id = str(uuid.uuid4())

    client.post(
        "/sync",
        json={
            "sessions": [
                {
                    "id": session_id,
                    "routine_day_id": ctx["routine_day_id"],
                    "started_at": _iso(),
                    "status": "in_progress",
                }
            ]
        },
    )

    # Two sets of the substituted exercise: performed=preferred, planned=Press banca.
    for set_number in (1, 2):
        client.post(
            "/sync",
            json={
                "set_logs": [
                    {
                        "id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "exercise_id": preferred,
                        "planned_exercise_id": ctx["exercise_id"],
                        "set_number": set_number,
                        "weight_kg": 60.0,
                        "reps": 8,
                        "created_at": _iso(),
                    }
                ]
            },
        )

    # The swap is counted once (not once per set); the preferred option now leads.
    alts = client.get(f"/exercises/{ctx['exercise_id']}/alternatives").json()
    picked = next(a for a in alts if a["id"] == preferred)
    assert picked["substitution_count"] == 1
    assert alts[0]["id"] == preferred  # ordered by prior use
