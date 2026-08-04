from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, utcnow


class SyncEvent(Base):
    """Server-side append-only outbox (spec §3).

    Every applied create/change writes one row here. `seq` (INTEGER PRIMARY KEY
    -> rowid, monotonic) is the pull cursor: a client asks for events with
    `seq > cursor`. Idempotency lives in the typed tables, so a re-pushed event
    that changes nothing does not append here.
    """

    __tablename__ = "sync_events"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    entity: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[str] = mapped_column(String(36))
    payload: Mapped[str] = mapped_column(Text)  # JSON of the entity's wire form
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
