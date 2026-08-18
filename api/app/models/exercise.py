from __future__ import annotations

from sqlalchemy import JSON, Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, new_uuid
from .enums import Equipment, MovementPattern


class Exercise(Base):
    """Shared catalogue entry (spec §4). `pattern` drives substitutions. `id` is
    a stable slug from the seed (e.g. "press-banca"), never regenerated."""

    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120))
    pattern: Mapped[MovementPattern] = mapped_column(
        SAEnum(MovementPattern, native_enum=False, length=32)
    )
    equipment: Mapped[Equipment] = mapped_column(
        SAEnum(Equipment, native_enum=False, length=20)
    )
    description: Mapped[str] = mapped_column(Text, default="")
    # Ordered cues for performing the lift, and the errors that most often
    # cost reps or cause injury. Lists rather than prose so the detail screen
    # can number the steps and mark the warnings separately.
    technique: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default=text("'[]'")
    )
    mistakes: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default=text("'[]'")
    )
    media_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_rest_s: Mapped[int] = mapped_column(Integer)
    # Logged/performed per leg or per side (e.g. bulgarian split squat).
    per_side: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("0")
    )
