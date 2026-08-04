from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ExercisePreference(Base):
    """Tracks how often a user swaps one exercise for another (spec §5.3).
    When `substitution_count` reaches 3, the app offers to make it permanent."""

    __tablename__ = "exercise_preferences"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    planned_exercise_id: Mapped[str] = mapped_column(
        ForeignKey("exercises.id"), primary_key=True
    )
    preferred_exercise_id: Mapped[str] = mapped_column(
        ForeignKey("exercises.id"), primary_key=True
    )
    substitution_count: Mapped[int] = mapped_column(Integer, default=0)
