"""Body weight (spec §5.6): the 7-day moving average is the only accionable
value; the raw daily weight swings with water and means nothing on its own."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..models import BodyWeight
from ..schemas import BodyWeightPoint, BodyWeightSummary

_HISTORY_DAYS = 120


def _window_avg(
    points: list[tuple[date, float]], end: date, span_days: int = 6
) -> float | None:
    start = end - timedelta(days=span_days)
    values = [w for (d, w) in points if start <= d <= end]
    return sum(values) / len(values) if values else None


def summary(db: OrmSession, user_id: str) -> BodyWeightSummary:
    rows = db.scalars(
        select(BodyWeight)
        .where(BodyWeight.user_id == user_id)
        .order_by(BodyWeight.measured_on)
    ).all()
    if not rows:
        return BodyWeightSummary(latest=None, avg7=None, delta_week=None, points=[])

    series = [(r.measured_on, float(r.weight_kg)) for r in rows]
    latest_date, latest = series[-1]

    avg7 = _window_avg(series, latest_date)
    prev = _window_avg(series, latest_date - timedelta(days=7))
    delta_week = (
        round(avg7 - prev, 1) if avg7 is not None and prev is not None else None
    )

    cutoff = latest_date - timedelta(days=_HISTORY_DAYS)
    points = [
        BodyWeightPoint(measured_on=d, weight_kg=w) for (d, w) in series if d >= cutoff
    ]
    return BodyWeightSummary(
        latest=round(latest, 1),
        avg7=round(avg7, 1) if avg7 is not None else None,
        delta_week=delta_week,
        points=points,
    )
