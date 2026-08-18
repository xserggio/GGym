"""The Inicio dashboard: one call, only numbers that change a decision.

Deliberately no streaks. The spec calls records "el refuerzo psicológico honesto,
frente a las rachas artificiales" (§7.2), and a streak counter would push
training on days the wheel says to rest. Everything here is measured, and any
figure that cannot be computed honestly (calories without a body weight) comes
back null so the UI can omit it rather than invent it.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import Session, SetLog
from ..models.base import utcnow
from ..models.enums import SessionStatus
from ..schemas import ActivityPoint, HomeOut
from . import bodyweight, stats, treadmill, wheel

# Selectable windows. None = all time.
PERIOD_DAYS: dict[str, int | None] = {
    "7d": 7,
    "30d": 30,
    "365d": 365,
    "all": None,
}
# Resistance training (Compendium of Physical Activities): a working set is hard
# but rests are not, so ~5 MET averaged over the session. Same constant the
# session summary uses, kept here so both screens agree.
RESISTANCE_MET = 5.0


def _activity(
    sessions: list[Session],
    volumes: dict[str, float],
    since: datetime | None,
    days: int | None,
) -> list[ActivityPoint]:
    """Work per bucket across the window, including the empty ones.

    Rest days are part of the picture — a chart that only plotted training days
    would hide the gaps, which is exactly what the user needs to see. Long
    windows bucket by month so the bar count stays readable.
    """
    by_month = days is None or days > 60
    tz_now = utcnow()
    start = since or (min((s.ended_at for s in sessions), default=tz_now))

    buckets: dict[date, ActivityPoint] = {}
    if by_month:
        cursor = start.date().replace(day=1)
        end = tz_now.date().replace(day=1)
        while cursor <= end:
            buckets[cursor] = ActivityPoint(bucket=cursor, sessions=0, volume_kg=0)
            cursor = (cursor + timedelta(days=32)).replace(day=1)
    else:
        for offset in range((days or 7)):
            day = (tz_now - timedelta(days=(days or 7) - 1 - offset)).date()
            buckets[day] = ActivityPoint(bucket=day, sessions=0, volume_kg=0)

    for session in sessions:
        if session.ended_at is None:
            continue
        key = session.ended_at.date().replace(day=1) if by_month else session.ended_at.date()
        point = buckets.get(key)
        if point is None:
            continue
        point.sessions += 1
        point.volume_kg = round(point.volume_kg + volumes.get(session.id, 0.0), 1)

    return list(buckets.values())


def _completed(
    db: OrmSession, user_id: str, since: datetime | None, until: datetime | None = None
) -> list[Session]:
    return list(
        db.scalars(
            select(Session).where(
                Session.user_id == user_id,
                Session.status == SessionStatus.completed,
                Session.ended_at.is_not(None),
                *([Session.ended_at >= since] if since is not None else []),
                *([Session.ended_at < until] if until is not None else []),
            )
        ).all()
    )


def _volume_of(db: OrmSession, sessions: list[Session]) -> tuple[float, int, dict[str, float]]:
    if not sessions:
        return 0.0, 0, {}
    rows = db.execute(
        select(SetLog.session_id, SetLog.weight_kg, SetLog.reps).where(
            SetLog.session_id.in_([s.id for s in sessions]),
            SetLog.voided.is_(False),
        )
    ).all()
    total, per_session = 0.0, {}
    for session_id, weight, reps in rows:
        volume = float(weight) * reps
        total += volume
        per_session[session_id] = per_session.get(session_id, 0.0) + volume
    return total, len(rows), per_session


def summary(db: OrmSession, user_id: str, period: str = "7d") -> HomeOut:
    days = PERIOD_DAYS.get(period, 7)
    since = utcnow() - timedelta(days=days) if days is not None else None

    sessions = _completed(db, user_id, since)

    strength_seconds = sum(
        int((s.ended_at - s.started_at).total_seconds())
        for s in sessions
        if s.ended_at is not None and s.started_at is not None
    )

    volume_kg, sets_done, per_session = _volume_of(db, sessions)

    # The same window immediately before, so every figure can say whether it is
    # up or down on your own recent form — a comparison the user has, unlike an
    # invented target. Undefined for "all time", which has no earlier window.
    prev_sessions_n: int | None = None
    prev_volume: float | None = None
    prev_treadmill_s: int | None = None
    if since is not None and days is not None:
        prev_since = since - timedelta(days=days)
        earlier = _completed(db, user_id, prev_since, since)
        prev_sessions_n = len(earlier)
        prev_volume = round(_volume_of(db, earlier)[0], 1)
        prev_treadmill_s = treadmill.seconds_since(
            db, user_id, prev_since
        ) - treadmill.seconds_since(db, user_id, since)

    weight = treadmill.latest_weight_kg(db, user_id)
    week_treadmill_s = treadmill.seconds_since(db, user_id, since)
    kcal = None
    if weight is not None:
        kcal = round(
            RESISTANCE_MET * weight * (strength_seconds / 3600)
            + (week_treadmill_s / 60) * treadmill.KCAL_PER_MIN_PER_KG * weight
        )

    last = db.scalar(
        select(func.max(Session.ended_at)).where(
            Session.user_id == user_id,
            Session.status == SessionStatus.completed,
        )
    )
    bw = bodyweight.summary(db, user_id)
    day = wheel.current_day_out(db, user_id)

    return HomeOut(
        period=period,
        next_position=day.position,
        next_day_name=day.name,
        next_exercises=len(day.exercises),
        week_sessions=len(sessions),
        week_sets=sets_done,
        week_volume_kg=round(volume_kg, 1),
        week_strength_seconds=strength_seconds,
        week_treadmill_seconds=week_treadmill_s,
        week_kcal=kcal,
        bodyweight_avg7=bw.avg7,
        bodyweight_delta_week=bw.delta_week,
        last_session_at=last,
        volume=stats.weekly_volume(db, user_id, days),
        records=stats.records(db, user_id)[:3],
        milestones=stats.milestones(db, user_id),
        activity=_activity(list(sessions), per_session, since, days),
        prev_sessions=prev_sessions_n,
        prev_volume_kg=prev_volume,
        prev_treadmill_seconds=prev_treadmill_s,
    )
