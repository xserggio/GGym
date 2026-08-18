"""Muscle recovery, recent load, and how much history they rest on.

The model has no sensor behind it, so the tests hold it to the two things that
make an estimate honest: it must never invent a reading it cannot support, and
the direction of every rule must be defensible out loud — more work means more
time, indirect work counts, and time heals.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Exercise, RoutineDay, Session, SetLog, User
from app.models.enums import SessionStatus
from app.services import muscles, recovery

NOW = datetime(2026, 8, 18, 12, 0, 0)


def _user_id(db) -> str:
    return db.scalar(select(User).where(User.username == "tester")).id


def log_session(db, user_id: str, exercise_name: str, sets: int, hours_ago: float):
    """A completed session of `sets` sets of one exercise, `hours_ago` back."""
    when = NOW - timedelta(hours=hours_ago)
    day = db.scalar(select(RoutineDay).where(RoutineDay.position == 1))
    exercise = db.scalar(select(Exercise).where(Exercise.name == exercise_name))
    assert exercise is not None, exercise_name
    session = Session(
        user_id=user_id,
        routine_day_id=day.id,
        status=SessionStatus.completed,
        started_at=when,
        ended_at=when,
    )
    db.add(session)
    db.flush()
    for number in range(1, sets + 1):
        db.add(
            SetLog(
                session_id=session.id,
                exercise_id=exercise.id,
                set_number=number,
                weight_kg=60,
                reps=8,
                created_at=when,
            )
        )
    db.commit()
    return exercise


def by_muscle(items) -> dict:
    return {m.muscle: m for m in items}


# --- refusing to invent --------------------------------------------------


def test_no_reading_at_all_without_training() -> None:
    """An all-green body would be technically true and completely useless: the
    app has simply never seen this person train."""
    with SessionLocal() as db:
        assert recovery.recovery(db, _user_id(db), NOW) is None


def test_load_stays_quiet_until_there_is_a_baseline() -> None:
    """A ratio against four days of history swings on a single session."""
    with SessionLocal() as db:
        user_id = _user_id(db)
        log_session(db, user_id, "Press banca", 4, hours_ago=48)
        assert recovery.load(db, user_id, NOW) is None


def test_confidence_reports_thin_history_as_thin() -> None:
    with SessionLocal() as db:
        user_id = _user_id(db)
        log_session(db, user_id, "Press banca", 4, hours_ago=48)
        thin = recovery.confidence(db, user_id, NOW)
        assert thin.sessions == 1
        assert not thin.solid

        for day in range(2, 12):
            log_session(db, user_id, "Press banca", 3, hours_ago=24 * day * 3)
        solid = recovery.confidence(db, user_id, NOW)
        assert solid.sessions >= recovery.SOLID_SESSIONS
        assert solid.baseline_days >= recovery.SOLID_DAYS
        assert solid.solid


# --- the rules the model claims ------------------------------------------


def test_a_hard_session_leaves_what_it_trained_loaded() -> None:
    with SessionLocal() as db:
        user_id = _user_id(db)
        log_session(db, user_id, "Press banca", 6, hours_ago=10)
        items = by_muscle(recovery.recovery(db, user_id, NOW))
    assert items["pecho"].band in ("cargado", "recuperando")
    assert items["pecho"].percent < 100
    # Nothing was asked of the legs.
    assert items["cuadriceps"].band == "fresco"
    assert items["cuadriceps"].percent == 100


def test_indirect_work_counts() -> None:
    """The morning after heavy pressing the triceps are not fresh, even though
    no triceps exercise appears anywhere in the session."""
    with SessionLocal() as db:
        user_id = _user_id(db)
        log_session(db, user_id, "Press banca", 6, hours_ago=10)
        items = by_muscle(recovery.recovery(db, user_id, NOW))
    assert items["triceps"].percent < 100
    # Still less beaten up than the muscle that did the work.
    assert items["triceps"].percent > items["pecho"].percent


def test_more_work_takes_longer() -> None:
    values = [recovery.hours_needed(n) for n in (2, 4, 8, 12, 30)]
    assert values == sorted(values)
    assert values[0] == recovery.MIN_HOURS
    assert values[-1] == recovery.MAX_HOURS


def test_time_heals() -> None:
    with SessionLocal() as db:
        user_id = _user_id(db)
        log_session(db, user_id, "Press banca", 6, hours_ago=10)
        soon = by_muscle(recovery.recovery(db, user_id, NOW))["pecho"].percent
        later = by_muscle(
            recovery.recovery(db, user_id, NOW + timedelta(hours=60))
        )["pecho"].percent
    assert later > soon
    assert later == 100


def test_the_least_recovered_bout_governs() -> None:
    """A hard session last week matters less than a light one yesterday: what
    stops you training today is the most recent debt, not the biggest."""
    with SessionLocal() as db:
        user_id = _user_id(db)
        log_session(db, user_id, "Press banca", 6, hours_ago=100)
        log_session(db, user_id, "Press banca", 3, hours_ago=6)
        pecho = by_muscle(recovery.recovery(db, user_id, NOW))["pecho"]
    assert pecho.percent < 60
    assert pecho.hours_to_fresh is not None and pecho.hours_to_fresh > 0


def test_every_muscle_is_reported_and_bands_match_numbers() -> None:
    with SessionLocal() as db:
        user_id = _user_id(db)
        log_session(db, user_id, "Press banca", 5, hours_ago=8)
        log_session(db, user_id, "Sentadilla", 5, hours_ago=30)
        items = recovery.recovery(db, user_id, NOW)
    assert {m.muscle for m in items} == set(muscles.MUSCLES)
    assert [m.percent for m in items] == sorted(m.percent for m in items)
    for item in items:
        assert 0 <= item.percent <= 100
        assert item.band == recovery.band_for(item.percent)
        # Only something short of fresh gets a countdown.
        assert (item.hours_to_fresh is None) == (item.percent >= recovery.FRESH_AT)


# --- recent load ---------------------------------------------------------


def test_load_reads_a_steady_month_as_balanced() -> None:
    with SessionLocal() as db:
        user_id = _user_id(db)
        for day in range(0, 28, 2):
            log_session(db, user_id, "Press banca", 5, hours_ago=24 * day + 2)
        balance = recovery.load(db, user_id, NOW)
    assert balance is not None
    assert balance.band == "equilibrada"
    assert 0.8 <= balance.ratio <= 1.3


def test_load_catches_a_week_that_ran_away() -> None:
    with SessionLocal() as db:
        user_id = _user_id(db)
        for day in range(8, 28, 3):  # a quiet month behind
            log_session(db, user_id, "Press banca", 3, hours_ago=24 * day)
        for day in range(0, 7):  # then a sudden heavy week
            log_session(db, user_id, "Press banca", 10, hours_ago=24 * day + 1)
        balance = recovery.load(db, user_id, NOW)
    assert balance is not None
    assert balance.ratio > recovery.BALANCED_TO
    assert balance.band in ("alta", "excesiva")


# --- the screen can say all of it ----------------------------------------


def test_endpoint_shapes_the_empty_case(client) -> None:
    body = client.get("/me/lab").json()
    assert body["recovery"] is None
    assert body["overall_percent"] is None
    assert body["load"] is None
    assert body["confidence"]["sessions"] == 0
    assert body["confidence"]["solid"] is False


def test_every_muscle_and_band_has_wording() -> None:
    from pathlib import Path

    i18n = Path(__file__).resolve().parents[2] / "web" / "src" / "i18n" / "es.ts"
    if not i18n.exists():
        return
    text = i18n.read_text(encoding="utf-8")
    for muscle in muscles.MUSCLES:
        assert f"{muscle}:" in text, muscle
    for band in ("cargado", "recuperando", "fresco"):
        assert f"{band}:" in text, band
    for band in ("baja", "equilibrada", "alta", "excesiva"):
        assert f"{band}:" in text, band
