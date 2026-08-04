from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, new_uuid, utcnow
from .enums import SessionStatus


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    routine_day_id: Mapped[str] = mapped_column(ForeignKey("routine_days.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, native_enum=False, length=16),
        default=SessionStatus.in_progress,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SetLog(Base):
    """Append-only event (spec §3). Never UPDATEd: a correction is a new row and
    the old one is flagged `voided`. `id` is client-generated for idempotent
    sync; the server default is only a fallback."""

    __tablename__ = "set_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    # Exercise actually performed.
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id"))
    # Exercise originally planned, when a substitution happened (spec §5.3).
    planned_exercise_id: Mapped[str | None] = mapped_column(
        ForeignKey("exercises.id"), nullable=True
    )
    set_number: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    reps: Mapped[int] = mapped_column(Integer)
    voided: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
