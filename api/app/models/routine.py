from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, new_uuid


class Routine(Base):
    __tablename__ = "routines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


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
