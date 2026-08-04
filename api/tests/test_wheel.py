"""The wheel wraps 1..N -> 1 and never depends on the calendar (spec §5.1)."""
from __future__ import annotations

from app.services.wheel import next_position


def test_advances_by_one() -> None:
    assert next_position(1, 5) == 2
    assert next_position(3, 5) == 4


def test_wraps_last_to_first() -> None:
    assert next_position(5, 5) == 1


def test_single_position_stays() -> None:
    assert next_position(1, 1) == 1


def test_empty_routine_is_noop() -> None:
    assert next_position(1, 0) == 1
