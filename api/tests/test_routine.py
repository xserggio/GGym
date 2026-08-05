"""Routine editing (spec pantalla 5)."""
from __future__ import annotations


def _first_day(client) -> dict:
    return client.get("/me/routine").json()["days"][0]


def test_edit_exercise_fields(client) -> None:
    rde = _first_day(client)["exercises"][0]
    resp = client.patch(
        f"/me/routine/exercises/{rde['id']}",
        json={"target_sets": 5, "rep_min": 3, "rep_max": 5, "rest_s": 180},
    )
    assert resp.status_code == 200
    updated = next(
        e for e in resp.json()["days"][0]["exercises"] if e["id"] == rde["id"]
    )
    assert (updated["target_sets"], updated["rep_min"], updated["rep_max"]) == (5, 3, 5)
    assert updated["rest_s"] == 180


def test_add_then_remove_exercise_renormalizes_order(client) -> None:
    day = _first_day(client)
    before = len(day["exercises"])
    exercise_id = client.get("/exercises").json()[0]["id"]

    added = client.post(
        f"/me/routine/days/{day['id']}/exercises",
        json={"exercise_id": exercise_id, "target_sets": 3, "rep_min": 8, "rep_max": 12},
    )
    assert added.status_code == 201
    day_after_add = next(d for d in added.json()["days"] if d["id"] == day["id"])
    assert len(day_after_add["exercises"]) == before + 1
    new_id = day_after_add["exercises"][-1]["id"]

    removed = client.delete(f"/me/routine/exercises/{new_id}")
    assert removed.status_code == 200
    day_after_remove = next(d for d in removed.json()["days"] if d["id"] == day["id"])
    assert len(day_after_remove["exercises"]) == before
    assert [e["order_index"] for e in day_after_remove["exercises"]] == list(range(before))


def test_reorder_exercises(client) -> None:
    day = _first_day(client)
    reversed_ids = [e["id"] for e in day["exercises"]][::-1]
    resp = client.put(
        f"/me/routine/days/{day['id']}/exercise-order", json={"ids": reversed_ids}
    )
    assert resp.status_code == 200
    day_after = next(d for d in resp.json()["days"] if d["id"] == day["id"])
    assert [e["id"] for e in day_after["exercises"]] == reversed_ids


def test_reorder_days_reassigns_positions(client) -> None:
    ids = [d["id"] for d in client.get("/me/routine").json()["days"]]
    rotated = ids[1:] + ids[:1]
    resp = client.put("/me/routine/day-order", json={"ids": rotated})
    assert resp.status_code == 200
    days = resp.json()["days"]
    assert [d["id"] for d in days] == rotated
    assert [d["position"] for d in days] == [1, 2, 3, 4, 5]


def test_rename_day(client) -> None:
    day = _first_day(client)
    resp = client.patch(f"/me/routine/days/{day['id']}", json={"name": "Empuje pesado"})
    assert resp.status_code == 200
    renamed = next(d for d in resp.json()["days"] if d["id"] == day["id"])
    assert renamed["name"] == "Empuje pesado"

    empty = client.patch(f"/me/routine/days/{day['id']}", json={"name": "  "})
    assert empty.status_code == 400


def test_reorder_rejects_non_permutation(client) -> None:
    day = _first_day(client)
    resp = client.put(
        f"/me/routine/days/{day['id']}/exercise-order", json={"ids": ["nope"]}
    )
    assert resp.status_code == 400
