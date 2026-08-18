"""Treadmill history (spec §5.5).

The stopwatch already stores each run; this reads them back so the work is
visible instead of vanishing after the timer resets. Calorie estimates use the
spec's formula, `min x 0.053 x kg` (~3 MET, walking at 4 km/h), and are omitted
when no body weight has been recorded — a guessed weight would be a fake number.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import BodyWeight, TreadmillSession
from ..models.base import utcnow
from ..schemas import TreadmillEntry, TreadmillSummary

KCAL_PER_MIN_PER_KG = 0.053
_HISTORY_LIMIT = 30


def latest_weight_kg(db: OrmSession, user_id: str) -> float | None:
    row = db.scalar(
        select(BodyWeight.weight_kg)
        .where(BodyWeight.user_id == user_id)
        .order_by(BodyWeight.measured_on.desc())
        .limit(1)
    )
    return float(row) if row is not None else None


def kcal_for(duration_s: int, weight_kg: float | None) -> int | None:
    if weight_kg is None:
        return None
    return round((duration_s / 60) * KCAL_PER_MIN_PER_KG * weight_kg)


def seconds_since(db: OrmSession, user_id: str, since: datetime | None) -> int:
    """Total treadmill seconds since `since`; all time when it is None."""
    return (
        db.scalar(
            select(func.coalesce(func.sum(TreadmillSession.duration_s), 0)).where(
                TreadmillSession.user_id == user_id,
                *([TreadmillSession.started_at >= since] if since is not None else []),
            )
        )
        or 0
    )


def week_seconds(db: OrmSession, user_id: str) -> int:
    return seconds_since(db, user_id, utcnow() - timedelta(days=7))


def summary(db: OrmSession, user_id: str) -> TreadmillSummary:
    weight = latest_weight_kg(db, user_id)
    rows = db.scalars(
        select(TreadmillSession)
        .where(TreadmillSession.user_id == user_id)
        .order_by(TreadmillSession.started_at.desc())
        .limit(_HISTORY_LIMIT)
    ).all()
    entries = [
        TreadmillEntry(
            id=row.id,
            started_at=row.started_at,
            duration_s=row.duration_s,
            kcal=kcal_for(row.duration_s, weight),
        )
        for row in rows
    ]
    total_s = (
        db.scalar(
            select(func.coalesce(func.sum(TreadmillSession.duration_s), 0)).where(
                TreadmillSession.user_id == user_id
            )
        )
        or 0
    )
    week_s = week_seconds(db, user_id)
    return TreadmillSummary(
        entries=entries,
        week_seconds=week_s,
        week_kcal=kcal_for(week_s, weight),
        total_seconds=total_s,
        sessions=len(rows),
    )
