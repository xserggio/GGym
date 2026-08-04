"""Body weight 7-day moving average (spec §5.6)."""
from __future__ import annotations

import uuid


def _push_weight(client, measured_on: str, kg: float) -> None:
    client.post(
        "/sync",
        json={
            "body_weights": [
                {"id": str(uuid.uuid4()), "measured_on": measured_on, "weight_kg": kg}
            ]
        },
    )


def test_empty_summary(client) -> None:
    data = client.get("/me/bodyweight").json()
    assert data == {"latest": None, "avg7": None, "delta_week": None, "points": []}


def test_moving_average_over_7_day_window(client) -> None:
    # Latest measured_on is 08-04; the 7-day window (07-29..08-04) covers all three.
    _push_weight(client, "2026-08-01", 80.0)
    _push_weight(client, "2026-08-03", 79.0)
    _push_weight(client, "2026-08-04", 78.0)

    data = client.get("/me/bodyweight").json()
    assert data["latest"] == 78.0  # raw latest, for the treadmill estimate
    assert data["avg7"] == 79.0  # (80 + 79 + 78) / 3
    assert len(data["points"]) == 3
