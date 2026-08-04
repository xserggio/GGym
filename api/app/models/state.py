from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserState(Base):
    """Per-user pointer into the wheel (spec §5.1).

    `next_position` only advances on a completed (or skipped) session, never by
    calendar date.
    """

    __tablename__ = "user_state"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    routine_id: Mapped[str] = mapped_column(ForeignKey("routines.id"))
    next_position: Mapped[int] = mapped_column(Integer, default=1)
    last_session_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
