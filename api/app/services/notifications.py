"""Daily training reminder (spec §7.6).

Adherence is the stated bottleneck, so the reminder is deliberately quiet: it
fires only on the days the routine suggests, only once per day, and never on a
day already trained. Delivery is Web Push signed with VAPID — a PWA cannot be
trusted to run a timer with the screen off (spec §6, background timers), so the
schedule lives on the server and a cron job drives it.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..config import get_settings
from ..models import (
    NotificationSetting,
    PushSubscription,
    RoutineDay,
    Session,
    User,
    UserState,
)
from ..models.enums import SessionStatus

log = logging.getLogger(__name__)

# A reminder is still worth sending shortly after its time (a cron tick may be
# late, the box may have been busy), but a stale one at midnight is just noise.
LATE_TOLERANCE_MIN = 90


@dataclass(frozen=True)
class DueReminder:
    user_id: str
    title: str
    body: str


def local_now() -> datetime:
    return datetime.now(ZoneInfo(get_settings().timezone))


def get_or_create_settings(db: OrmSession, user_id: str) -> NotificationSetting:
    row = db.get(NotificationSetting, user_id)
    if row is None:
        row = NotificationSetting(user_id=user_id)
        db.add(row)
        db.flush()
    return row


def _trained_today(db: OrmSession, user_id: str, today: date) -> bool:
    """Completed sessions are stored in UTC; compare against the local day by
    widening the window a day either side and matching on the local date."""
    rows = db.scalars(
        select(Session.ended_at).where(
            Session.user_id == user_id,
            Session.status == SessionStatus.completed,
            Session.ended_at.is_not(None),
            Session.ended_at >= datetime.combine(today, datetime.min.time())
            - timedelta(days=1),
        )
    ).all()
    tz = ZoneInfo(get_settings().timezone)
    return any(
        ended.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz).date() == today
        for ended in rows
    )


def _is_suggested_day(db: OrmSession, user_id: str, weekday: int) -> tuple[bool, str]:
    """Whether today is the suggested day for the session the wheel points at.

    Returns (should_notify, day_name). Days with no `suggested_dow` never
    trigger a reminder — the user hasn't said when they train it.
    """
    state = db.get(UserState, user_id)
    if state is None:
        return False, ""
    day = db.scalar(
        select(RoutineDay).where(
            RoutineDay.routine_id == state.routine_id,
            RoutineDay.position == state.next_position,
        )
    )
    if day is None or day.suggested_dow is None:
        return False, ""
    return day.suggested_dow == weekday, day.name


def due_reminders(db: OrmSession, now: datetime | None = None) -> list[DueReminder]:
    """Users whose reminder is due right now and hasn't been sent today."""
    now = now or local_now()
    today = now.date()
    minutes_now = now.hour * 60 + now.minute
    weekday = now.isoweekday()  # 1 = Monday, matching seed `suggested_dow`

    due: list[DueReminder] = []
    for setting in db.scalars(
        select(NotificationSetting).where(NotificationSetting.enabled.is_(True))
    ).all():
        if setting.last_sent_on == today:
            continue
        delta = minutes_now - (setting.hour * 60 + setting.minute)
        if delta < 0 or delta > LATE_TOLERANCE_MIN:
            continue
        if _trained_today(db, setting.user_id, today):
            continue
        suggested, day_name = _is_suggested_day(db, setting.user_id, weekday)
        if not suggested:
            continue
        state = db.get(UserState, setting.user_id)
        position = state.next_position if state else 0
        due.append(
            DueReminder(
                user_id=setting.user_id,
                title="hoy toca entrenar",
                body=f"sesión {position} · {day_name}",
            )
        )
    return due


def send_to_user(db: OrmSession, reminder: DueReminder) -> int:
    """Push to every device of a user. Returns how many were delivered.

    Endpoints rejected as gone (404/410) are deleted: that device uninstalled
    the app or reset its subscription, and keeping it would retry forever.
    """
    from pywebpush import WebPushException, webpush  # heavy import, only when sending

    settings = get_settings()
    if not settings.vapid_private_key:
        log.warning("push not configured (no VAPID key); nothing sent")
        return 0

    subs = db.scalars(
        select(PushSubscription).where(PushSubscription.user_id == reminder.user_id)
    ).all()
    sent = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=json.dumps({"title": reminder.title, "body": reminder.body}),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
            sent += 1
        except WebPushException as exc:
            status_code = getattr(exc.response, "status_code", None)
            if status_code in (404, 410):
                db.delete(sub)
                log.info("dropped expired push subscription for %s", reminder.user_id)
            else:
                log.warning("push failed for %s: %s", reminder.user_id, exc)
        except Exception as exc:  # noqa: BLE001
            # A network error (DNS, timeout, TLS) must not abort the cron run:
            # everyone queued behind this device would silently lose their
            # reminder. Skip the device and carry on.
            log.warning("push error for %s: %s", reminder.user_id, exc)
    return sent


def run_due(db: OrmSession, now: datetime | None = None) -> int:
    """Send every due reminder and mark it sent. Returns pushes delivered."""
    now = now or local_now()
    total = 0
    for reminder in due_reminders(db, now):
        delivered = send_to_user(db, reminder)
        total += delivered
        # Mark the day as handled even when no device was reachable, so a
        # subscription-less user doesn't get retried every cron tick.
        get_or_create_settings(db, reminder.user_id).last_sent_on = now.date()
    db.commit()
    return total


def subscribe(
    db: OrmSession, user: User, endpoint: str, p256dh: str, auth: str
) -> PushSubscription:
    """Register a device. Endpoints are unique, so re-subscribing the same
    browser refreshes its keys instead of creating a duplicate."""
    existing = db.scalar(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    )
    if existing is not None:
        existing.user_id = user.id
        existing.p256dh = p256dh
        existing.auth = auth
        return existing
    sub = PushSubscription(
        user_id=user.id, endpoint=endpoint, p256dh=p256dh, auth=auth
    )
    db.add(sub)
    db.flush()
    return sub
