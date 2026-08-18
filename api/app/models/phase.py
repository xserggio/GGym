from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum as SAEnum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, new_uuid


class PhaseKind(str, enum.Enum):
    """What the body weight is meant to be doing. The app never causes any of
    these — diet does — it only measures whether the outcome matches the
    intent and adapts what it expects from training."""

    superavit = "superavit"
    definicion = "definicion"
    mantenimiento = "mantenimiento"


class Phase(Base):
    """A declared training phase. Closed phases stay for the record: knowing a
    lift was set during a deficit is part of reading it correctly."""

    __tablename__ = "phases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[PhaseKind] = mapped_column(
        SAEnum(PhaseKind, native_enum=False, length=20)
    )
    started_on: Mapped[date] = mapped_column(Date)
    # Null while the phase is the active one.
    ended_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Intended change in body weight, as a percentage of body weight per week.
    # Negative for a deficit. Stored per phase so changing the target later does
    # not rewrite how earlier weeks were judged.
    target_rate_pct: Mapped[float] = mapped_column(Float)
    # Optional date the user is aiming at (a holiday, the summer), and the
    # weight that goes with it. Both are needed to say whether the plan is
    # arithmetically possible; a date on its own is only a countdown.
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
