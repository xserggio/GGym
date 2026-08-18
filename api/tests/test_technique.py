"""Every catalogue exercise carries execution cues and common errors: a detail
screen that shows nothing for some lifts is worse than one that shows none."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from seed.load import TECHNIQUE_JSON, load_data, load_technique


def test_every_seeded_exercise_has_cues() -> None:
    technique = load_technique()
    for path in (None, "seed/routine_gigi.json"):
        for item in load_data(path)["exercises"]:
            cues = technique.get(item["id"])
            assert cues is not None, f"{item['id']} has no technique entry"
            assert len(cues["technique"]) >= 3, item["id"]
            assert len(cues["mistakes"]) >= 2, item["id"]


def test_cues_are_exposed_by_the_api(client: TestClient) -> None:
    body = client.get("/exercises/press-banca").json()
    assert len(body["technique"]) >= 3
    assert len(body["mistakes"]) >= 2
    # Assert the shape and the house voice, not a specific wording: pinning a
    # word makes the test fail on a spelling fix rather than on a real problem.
    for step in body["technique"] + body["mistakes"]:
        assert step == step.strip() and len(step) > 15
        assert not step.endswith(".") and "!" not in step


def test_no_orphan_entries() -> None:
    """A cue for an exercise that no longer exists is dead weight."""
    seeded = {
        item["id"]
        for path in (None, "seed/routine_gigi.json")
        for item in load_data(path)["exercises"]
    }
    orphans = set(load_technique()) - seeded
    assert orphans == set(), orphans


def test_technique_file_is_valid_json() -> None:
    json.loads(TECHNIQUE_JSON.read_text(encoding="utf-8"))
