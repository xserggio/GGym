from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class NotificationSetting(Base):
    """Daily training reminder (spec §7.6). Adherence is the stated bottleneck.

    The hour is local wall-clock time in the user's timezone; the sender runs
    often and compares against it. `last_sent_on` makes sending idempotent, so a
    cron that fires every few minutes still delivers exactly one push per day.
    """

    __tablename__ = "notification_settings"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    hour: Mapped[int] = mapped_column(Integer, default=18)
    minute: Mapped[int] = mapped_column(Integer, default=0)
    last_sent_on: Mapped[date | None] = mapped_column(Date, nullable=True)


class PushSubscription(Base):
    """A browser push endpoint. One row per device; a user may have several."""

    __tablename__ = "push_subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    endpoint: Mapped[str] = mapped_column(String(512), unique=True)
    p256dh: Mapped[str] = mapped_column(String(255))
    auth: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
