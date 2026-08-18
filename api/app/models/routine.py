from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, new_uuid


class Routine(Base):
    """A routine profile. A user may keep several and switch between them; only
    one is `active` at a time. Old profiles are never deleted implicitly —
    sessions point at their days, and losing them would lose history."""

    __tablename__ = "routines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # The pristine seeded routine, kept read-only so "restore defaults" always
    # has something true to copy from. Never edited, never activated directly.
    is_original: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RoutineDay(Base):
    """A wheel position ("sesión 1..5"). `position` is the wheel order;
    `suggested_dow` is purely informational (spec §5.1)."""

    __tablename__ = "routine_days"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    routine_id: Mapped[str] = mapped_column(ForeignKey("routines.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(120))
    suggested_dow: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RoutineDayExercise(Base):
    __tablename__ = "routine_day_exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    routine_day_id: Mapped[str] = mapped_column(
        ForeignKey("routine_days.id"), index=True
    )
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id"))
    order_index: Mapped[int] = mapped_column(Integer)
    target_sets: Mapped[int] = mapped_column(Integer)
    rep_min: Mapped[int] = mapped_column(Integer)
    rep_max: Mapped[int] = mapped_column(Integer)
    # Null => fall back to Exercise.default_rest_s
    rest_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # "reps" or "seconds" (time-based holds like the plank).
    unit: Mapped[str] = mapped_column(
        String(10), default="reps", server_default=text("'reps'")
    )
