"""The daily reminder is quiet by design (spec §7.6): only on the suggested day
for the session the wheel points at, once per day, and never after training."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.models import PushSubscription, RoutineDay, Session, UserState
from app.models.base import utcnow
from app.models.enums import SessionStatus
from app.services import notifications

MADRID = ZoneInfo("Europe/Madrid")


def _enable(user_id: str, hour: int = 18, minute: int = 0) -> None:
    with SessionLocal() as db:
        setting = notifications.get_or_create_settings(db, user_id)
        setting.enabled = True
        setting.hour = hour
        setting.minute = minute
        db.commit()


def _suggested_dow_for_pointer(user_id: str) -> int:
    with SessionLocal() as db:
        state = db.get(UserState, user_id)
        day = db.scalar(
            select(RoutineDay).where(
                RoutineDay.routine_id == state.routine_id,
                RoutineDay.position == state.next_position,
            )
        )
        return day.suggested_dow


def _at(dow: int, hour: int, minute: int = 0) -> datetime:
    """A datetime whose ISO weekday is `dow`, in the reminder timezone."""
    base = datetime(2026, 8, 3, hour, minute, tzinfo=MADRID)  # a Monday
    return base + timedelta(days=dow - 1)


def test_fires_on_the_suggested_day_at_the_set_time(ctx: dict) -> None:
    _enable(ctx["user_id"])
    dow = _suggested_dow_for_pointer(ctx["user_id"])
    with SessionLocal() as db:
        due = notifications.due_reminders(db, _at(dow, 18, 0))
    assert [d.user_id for d in due] == [ctx["user_id"]]
    assert "sesión 1" in due[0].body


def test_silent_before_the_set_time(ctx: dict) -> None:
    _enable(ctx["user_id"], hour=18)
    dow = _suggested_dow_for_pointer(ctx["user_id"])
    with SessionLocal() as db:
        assert notifications.due_reminders(db, _at(dow, 17, 30)) == []


def test_silent_long_after_the_set_time(ctx: dict) -> None:
    """A missed reminder is dropped, not delivered at midnight."""
    _enable(ctx["user_id"], hour=18)
    dow = _suggested_dow_for_pointer(ctx["user_id"])
    with SessionLocal() as db:
        assert notifications.due_reminders(db, _at(dow, 23, 59)) == []


def test_silent_on_a_rest_day(ctx: dict) -> None:
    _enable(ctx["user_id"])
    dow = _suggested_dow_for_pointer(ctx["user_id"])
    other = (dow % 7) + 1
    with SessionLocal() as db:
        assert notifications.due_reminders(db, _at(other, 18, 0)) == []


def test_silent_when_disabled(ctx: dict) -> None:
    dow = _suggested_dow_for_pointer(ctx["user_id"])
    with SessionLocal() as db:  # never enabled
        assert notifications.due_reminders(db, _at(dow, 18, 0)) == []


def test_silent_after_training_today(ctx: dict) -> None:
    _enable(ctx["user_id"])
    dow = _suggested_dow_for_pointer(ctx["user_id"])
    now = _at(dow, 18, 0)
    with SessionLocal() as db:
        db.add(
            Session(
                user_id=ctx["user_id"],
                routine_day_id=ctx["routine_day_id"],
                status=SessionStatus.completed,
                started_at=now.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
                ended_at=now.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
            )
        )
        db.commit()
    with SessionLocal() as db:
        assert notifications.due_reminders(db, now) == []


def test_sent_once_per_day(ctx: dict) -> None:
    _enable(ctx["user_id"])
    dow = _suggested_dow_for_pointer(ctx["user_id"])
    now = _at(dow, 18, 0)
    with SessionLocal() as db:
        notifications.get_or_create_settings(db, ctx["user_id"]).last_sent_on = now.date()
        db.commit()
    with SessionLocal() as db:
        assert notifications.due_reminders(db, now) == []


def test_settings_roundtrip_and_rearm(client: TestClient) -> None:
    assert client.get("/me/notifications").json()["enabled"] is False
    resp = client.patch(
        "/me/notifications", json={"enabled": True, "hour": 7, "minute": 30}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert (body["enabled"], body["hour"], body["minute"]) == (True, 7, 30)
    assert body["devices"] == 0


def test_rejects_impossible_time(client: TestClient) -> None:
    resp = client.patch(
        "/me/notifications", json={"enabled": True, "hour": 25, "minute": 0}
    )
    assert resp.status_code == 422


def test_subscribe_is_idempotent_per_endpoint(client: TestClient) -> None:
    payload = {
        "endpoint": "https://push.example/abc",
        "keys": {"p256dh": "key-1", "auth": "auth-1"},
    }
    assert client.post("/me/notifications/subscribe", json=payload).json()["devices"] == 1
    payload["keys"]["p256dh"] = "key-2"
    assert client.post("/me/notifications/subscribe", json=payload).json()["devices"] == 1

    resp = client.delete(
        "/me/notifications/subscribe", params={"endpoint": payload["endpoint"]}
    )
    assert resp.status_code == 204
    assert client.get("/me/notifications").json()["devices"] == 0


def test_network_error_on_one_device_does_not_abort_the_run(
    ctx: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dead endpoint must not cost everyone else their reminder."""
    import pywebpush

    _enable(ctx["user_id"])
    dow = _suggested_dow_for_pointer(ctx["user_id"])
    now = _at(dow, 18, 0)
    with SessionLocal() as db:
        db.add(
            PushSubscription(
                user_id=ctx["user_id"],
                endpoint="https://unreachable.invalid/x",
                p256dh="k",
                auth="a",
            )
        )
        db.commit()

    def boom(*args: object, **kwargs: object) -> None:
        raise ConnectionError("dns failure")

    monkeypatch.setattr(pywebpush, "webpush", boom)

    with SessionLocal() as db:
        assert notifications.run_due(db, now) == 0  # no crash
    # The day is still marked handled, so the cron doesn't retry every 10 min.
    with SessionLocal() as db:
        assert notifications.get_or_create_settings(db, ctx["user_id"]).last_sent_on == now.date()
