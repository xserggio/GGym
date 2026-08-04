from __future__ import annotations

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, new_uuid
from .enums import Equipment, MovementPattern


class Exercise(Base):
    """Shared catalogue entry (spec §4). `pattern` drives substitutions."""

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
    media_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_rest_s: Mapped[int] = mapped_column(Integer)
