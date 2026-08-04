"""Declarative base, shared column helpers and constraint naming.

A deterministic naming convention keeps Alembic autogenerate stable across
machines: constraint names are derived from table/column, never auto-numbered.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def new_uuid() -> str:
    """Server-side UUID default. Client-generated events supply their own."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Naive UTC. SQLite has no tz storage, so we keep everything naive-UTC to
    avoid mixing aware and naive datetimes in comparisons."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(value: datetime) -> datetime:
    """Normalize a possibly tz-aware datetime (e.g. from a client) to naive UTC."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value
