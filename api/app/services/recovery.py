"""How recovered each muscle is, estimated from the sets that were logged.

This is the one screen in the app that shows a number nobody measured. Helix and
the wearables behind it read recovery from heart-rate variability; GGym has no
sensor and never will, so what it has instead is the training itself: what was
worked, how much of it, and how long ago.

That is enough for a defensible estimate and not enough to pretend precision.
Two rules keep it honest. The clock scales with the dose — four sets of an
accessory are not three days of soreness, and twelve sets of squats are not gone
by morning — and the answer is labelled an estimate everywhere it appears,
because the app cannot know whether someone slept, ate or is coming down with
something.

The muscle split is the same one the routine assistant uses, so a set of bench
press recovers the chest *and* the triceps. Counting only direct work would show
fresh triceps the morning after a heavy pressing session.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import Exercise, Session, SetLog
from ..models.base import utcnow
from ..models.enums import SessionStatus
from . import muscles

# How long a muscle needs before it is ready for real work again, by how much it
# got. The span is the usual 24-72h: a light accessory dose clears overnight, a
# hard compound session takes most of three days.
MIN_HOURS = 24.0
MAX_HOURS = 72.0
HOURS_PER_SET = 6.0
SETS_AT_MIN = 4.0

# Only the last few days can still be holding a muscle down; beyond that the
# arithmetic would say "fresh" anyway.
WINDOW_DAYS = 8

# The same three bands the volume view uses, so "cargado" reads the same way
# wherever it appears.
FATIGUED_BELOW = 60.0
FRESH_AT = 86.0


@dataclass
class MuscleRecovery:
    muscle: str
    # 0-100. 100 means nothing recent is still being paid off.
    percent: float
    # cargado | recuperando | fresco — a key the UI translates.
    band: str
    # Hours until this muscle reaches `FRESH_AT`; None when it is already there.
    hours_to_fresh: float | None


def band_for(percent: float) -> str:
    if percent < FATIGUED_BELOW:
        return "cargado"
    if percent < FRESH_AT:
        return "recuperando"
    return "fresco"


def hours_needed(effective_sets: float) -> float:
    """The recovery clock for one bout. Deliberately blunt: the point is that a
    bigger dose costs more time, not that six hours per set is a measured
    constant."""
    hours = MIN_HOURS + (effective_sets - SETS_AT_MIN) * HOURS_PER_SET
    return max(MIN_HOURS, min(MAX_HOURS, hours))


def _bouts(
    db: OrmSession, user_id: str, since: datetime
) -> dict[str, list[tuple[datetime, float]]]:
    """Effective sets per muscle per session, with when that session happened.

    Grouped by session rather than by set: a session is one bout of work, and
    spreading its sets across the evening does not make each one its own
    stimulus.
    """
    rows = db.execute(
        select(
            SetLog.session_id,
            func.max(SetLog.created_at),
            Exercise.pattern,
            func.count(SetLog.id),
        )
        .join(Session, Session.id == SetLog.session_id)
        .join(Exercise, Exercise.id == SetLog.exercise_id)
        .where(
            Session.user_id == user_id,
            SetLog.voided.is_(False),
            SetLog.created_at >= since,
        )
        .group_by(SetLog.session_id, Exercise.pattern)
    ).all()

    per_muscle: dict[str, dict[str, tuple[datetime, float]]] = {}
    for session_id, when, pattern, count in rows:
        for muscle, weight in muscles.CONTRIBUTION.get(pattern, {}).items():
            bucket = per_muscle.setdefault(muscle, {})
            at, total = bucket.get(session_id, (when, 0.0))
            bucket[session_id] = (max(at, when), total + count * weight)
    return {m: list(sessions.values()) for m, sessions in per_muscle.items()}


def recovery(
    db: OrmSession, user_id: str, now: datetime | None = None
) -> list[MuscleRecovery] | None:
    """Recovery per muscle, ordered most loaded first.

    None when there is no training logged at all: a full row of green would be
    technically true and completely useless, and it would be the app's first
    number that means nothing.
    """
    now = now or utcnow()
    trained = db.scalar(
        select(func.count())
        .select_from(Session)
        .where(Session.user_id == user_id, Session.status == SessionStatus.completed)
    )
    if not trained:
        return None

    bouts = _bouts(db, user_id, now - timedelta(days=WINDOW_DAYS))
    out: list[MuscleRecovery] = []
    for muscle in muscles.MUSCLES:
        worst = 1.0
        remaining = 0.0
        for when, effective in bouts.get(muscle, []):
            if effective <= 0:
                continue
            needed = hours_needed(effective)
            elapsed = max((now - when).total_seconds() / 3600, 0.0)
            # The bout that is furthest from being paid off governs: a light
            # session yesterday leaves you less ready than a hard one last week.
            share = min(elapsed / needed, 1.0)
            if share < worst:
                worst = share
                remaining = max(needed * (FRESH_AT / 100) - elapsed, 0.0)
        percent = round(worst * 100, 1)
        out.append(
            MuscleRecovery(
                muscle=muscle,
                percent=percent,
                band=band_for(percent),
                hours_to_fresh=round(remaining, 1) if percent < FRESH_AT else None,
            )
        )
    out.sort(key=lambda m: m.percent)
    return out


def overall(items: list[MuscleRecovery]) -> float:
    return round(sum(m.percent for m in items) / len(items), 1) if items else 100.0


# --- recent load ---------------------------------------------------------
#
# Acute versus chronic: this week's work against the average week behind it.
# It is the standard way to catch a ramp that outruns what the body has been
# prepared for, and it needs no sensor — only the sets already in the database.

ACUTE_DAYS = 7
CHRONIC_DAYS = 28
# Below this much history the ratio compares a week against almost nothing and
# swings wildly, so it is not shown at all.
MIN_DAYS_FOR_RATIO = 14

BALANCED_FROM = 0.8
BALANCED_TO = 1.3
HIGH_TO = 1.5


@dataclass
class Load:
    ratio: float
    # baja | equilibrada | alta | excesiva
    band: str
    acute_sets: int
    chronic_weekly_sets: float


def _sets_between(
    db: OrmSession, user_id: str, since: datetime, until: datetime
) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(SetLog)
            .join(Session, Session.id == SetLog.session_id)
            .where(
                Session.user_id == user_id,
                SetLog.voided.is_(False),
                SetLog.created_at >= since,
                SetLog.created_at < until,
            )
        )
        or 0
    )


def first_logged(db: OrmSession, user_id: str) -> datetime | None:
    return db.scalar(
        select(func.min(SetLog.created_at))
        .join(Session, Session.id == SetLog.session_id)
        .where(Session.user_id == user_id, SetLog.voided.is_(False))
    )


def load(db: OrmSession, user_id: str, now: datetime | None = None) -> Load | None:
    now = now or utcnow()
    first = first_logged(db, user_id)
    if first is None or (now - first).days < MIN_DAYS_FOR_RATIO:
        return None

    acute = _sets_between(db, user_id, now - timedelta(days=ACUTE_DAYS), now)
    # The chronic window covers the acute one on purpose: the comparison is
    # against your own recent normal, which includes this week.
    span_days = min((now - first).days, CHRONIC_DAYS)
    chronic_total = _sets_between(db, user_id, now - timedelta(days=span_days), now)
    weekly = chronic_total / (span_days / 7)
    if weekly <= 0:
        return None

    ratio = acute / weekly
    band = (
        "baja"
        if ratio < BALANCED_FROM
        else "equilibrada"
        if ratio <= BALANCED_TO
        else "alta"
        if ratio <= HIGH_TO
        else "excesiva"
    )
    return Load(
        ratio=round(ratio, 2),
        band=band,
        acute_sets=acute,
        chronic_weekly_sets=round(weekly, 1),
    )


# --- how much this is built on -------------------------------------------

# Under this, the readings above are drawn from a short and lumpy history and
# the UI says so rather than presenting them with the same confidence.
SOLID_SESSIONS = 8
SOLID_DAYS = 28


@dataclass
class Confidence:
    sessions: int
    baseline_days: int
    # True once there is enough history for the numbers to mean much.
    solid: bool


def confidence(
    db: OrmSession, user_id: str, now: datetime | None = None
) -> Confidence:
    now = now or utcnow()
    sessions = (
        db.scalar(
            select(func.count())
            .select_from(Session)
            .where(
                Session.user_id == user_id,
                Session.status == SessionStatus.completed,
            )
        )
        or 0
    )
    first = first_logged(db, user_id)
    days = (now - first).days if first else 0
    return Confidence(
        sessions=sessions,
        baseline_days=days,
        solid=sessions >= SOLID_SESSIONS and days >= SOLID_DAYS,
    )


# --- what today's session will ask for -----------------------------------
#
# The wheel already knows which session is next and the map above knows how
# recovered everything is; crossing them is what turns a diagram into advice.
# Only muscles the session actually trains appear, so a leg day never mentions
# a sore chest.

# A muscle has to take a real share of the session to be worth naming: bench
# press works the shoulders, but a shoulder at 40% is not a reason to skip it.
MIN_SHARE_OF_SESSION = 0.12


@dataclass
class TodayMuscle:
    muscle: str
    percent: float
    band: str
    # Effective sets this session puts on it.
    sets: float


@dataclass
class TodayLoad:
    day_name: str
    position: int
    muscles: list[TodayMuscle]
    # listo | justo | cargado — how the least recovered of them looks.
    verdict: str


def today_load(
    db: OrmSession, user_id: str, items: list[MuscleRecovery] | None
) -> TodayLoad | None:
    from ..models import Routine, RoutineDay, RoutineDayExercise, UserState

    if not items:
        return None
    state = db.get(UserState, user_id)
    if state is None:
        return None
    routine_id = db.scalar(
        select(Routine.id).where(Routine.user_id == user_id, Routine.active.is_(True))
    )
    day = db.scalar(
        select(RoutineDay).where(
            RoutineDay.routine_id == routine_id,
            RoutineDay.position == state.next_position,
        )
    )
    if day is None:
        return None

    rows = db.execute(
        select(Exercise.pattern, RoutineDayExercise.target_sets)
        .join(Exercise, Exercise.id == RoutineDayExercise.exercise_id)
        .where(RoutineDayExercise.routine_day_id == day.id)
    ).all()
    effective: dict[str, float] = {}
    for pattern, sets in rows:
        for muscle, weight in muscles.CONTRIBUTION.get(pattern, {}).items():
            effective[muscle] = effective.get(muscle, 0.0) + sets * weight
    total = sum(effective.values())
    if total <= 0:
        return None

    by_muscle = {m.muscle: m for m in items}
    trained = [
        TodayMuscle(
            muscle=muscle,
            percent=by_muscle[muscle].percent,
            band=by_muscle[muscle].band,
            sets=round(sets, 1),
        )
        for muscle, sets in effective.items()
        if muscle in by_muscle and sets / total >= MIN_SHARE_OF_SESSION
    ]
    if not trained:
        return None
    trained.sort(key=lambda m: m.percent)

    worst = trained[0].percent
    verdict = (
        "cargado" if worst < FATIGUED_BELOW else "justo" if worst < FRESH_AT else "listo"
    )
    return TodayLoad(
        day_name=day.name, position=day.position, muscles=trained, verdict=verdict
    )


# --- lifts that stopped moving -------------------------------------------
#
# "Stalled" is a strong claim and easy to get wrong, so it has to clear five
# gates before the app will say it. Calling a lift stalled that was never
# really trained would teach the user to ignore the screen, which costs more
# than staying quiet.

MIN_SESSIONS_FOR_STALL = 5
RECENT_SESSIONS = 4
# Past this without touching it, a lift is abandoned rather than stuck, and
# telling someone their bench is stalled six months on would just be wrong.
STALE_AFTER_DAYS = 56


@dataclass
class Stalled:
    exercise_id: str
    exercise_name: str
    sessions: int
    days_since_best: int


def _holding_load_by_design(db: OrmSession, user_id: str) -> bool:
    """During a cut the app deliberately stops pushing weight (progression.py),
    so a flat line is the plan working, not a problem."""
    from ..models import Phase
    from ..models.phase import PhaseKind

    phase = db.scalars(
        select(Phase).where(Phase.user_id == user_id, Phase.ended_on.is_(None))
    ).first()
    return phase is not None and phase.kind == PhaseKind.definicion


def stalled(
    db: OrmSession, user_id: str, now: datetime | None = None
) -> list[Stalled]:
    from ..models import Routine, RoutineDay, RoutineDayExercise

    now = now or utcnow()
    if _holding_load_by_design(db, user_id):
        return []

    # Gate 1: only lifts that are actually in the routine right now.
    routine_id = db.scalar(
        select(Routine.id).where(Routine.user_id == user_id, Routine.active.is_(True))
    )
    planned = set(
        db.scalars(
            select(RoutineDayExercise.exercise_id)
            .join(RoutineDay, RoutineDay.id == RoutineDayExercise.routine_day_id)
            .where(RoutineDay.routine_id == routine_id)
        ).all()
    )
    if not planned:
        return []

    rows = db.execute(
        select(
            SetLog.exercise_id,
            Exercise.name,
            SetLog.created_at,
            SetLog.weight_kg,
            SetLog.reps,
        )
        .join(Session, Session.id == SetLog.session_id)
        .join(Exercise, Exercise.id == SetLog.exercise_id)
        .where(
            Session.user_id == user_id,
            SetLog.voided.is_(False),
            SetLog.exercise_id.in_(planned),
        )
    ).all()

    # Best estimated 1RM per day, per exercise.
    best: dict[str, dict] = {}
    names: dict[str, str] = {}
    for exercise_id, name, when, weight, reps in rows:
        names[exercise_id] = name
        day = when.date()
        one_rm = float(weight) * (1 + reps / 30)
        per_day = best.setdefault(exercise_id, {})
        if one_rm > per_day.get(day, 0):
            per_day[day] = one_rm

    out: list[Stalled] = []
    for exercise_id, per_day in best.items():
        # Gate 2: enough sessions to have an opinion at all.
        if len(per_day) < MIN_SESSIONS_FOR_STALL:
            continue
        days = sorted(per_day)
        # Gate 3: still part of the current training, not something dropped.
        if (now.date() - days[-1]).days > STALE_AFTER_DAYS:
            continue
        values = [per_day[d] for d in days]
        recent, earlier = values[-RECENT_SESSIONS:], max(values[:-RECENT_SESSIONS])
        # Gate 4: the recent block genuinely failed to beat what came before.
        if max(recent) > earlier:
            continue
        peak_day = max(days, key=lambda d: per_day[d])
        out.append(
            Stalled(
                exercise_id=exercise_id,
                exercise_name=names[exercise_id],
                sessions=len(per_day),
                days_since_best=(now.date() - peak_day).days,
            )
        )
    out.sort(key=lambda s: s.days_since_best, reverse=True)
    return out


# --- weekly volume per muscle, over time ---------------------------------

TREND_WEEKS = 8


@dataclass
class MuscleTrend:
    muscle: str
    # Effective sets per week, oldest first; always TREND_WEEKS long.
    weekly: list[float]
    # sube | estable | baja, comparing the recent half against the earlier one.
    trend: str


def volume_trend(
    db: OrmSession, user_id: str, now: datetime | None = None
) -> list[MuscleTrend] | None:
    now = now or utcnow()
    first = first_logged(db, user_id)
    if first is None:
        return None
    since = now - timedelta(weeks=TREND_WEEKS)
    rows = db.execute(
        select(SetLog.created_at, Exercise.pattern, func.count(SetLog.id))
        .join(Session, Session.id == SetLog.session_id)
        .join(Exercise, Exercise.id == SetLog.exercise_id)
        .where(
            Session.user_id == user_id,
            SetLog.voided.is_(False),
            SetLog.created_at >= since,
        )
        .group_by(SetLog.created_at, Exercise.pattern)
    ).all()

    buckets: dict[str, list[float]] = {m: [0.0] * TREND_WEEKS for m in muscles.MUSCLES}
    for when, pattern, count in rows:
        index = min(int((when - since).days / 7), TREND_WEEKS - 1)
        for muscle, weight in muscles.CONTRIBUTION.get(pattern, {}).items():
            buckets[muscle][index] += count * weight

    half = TREND_WEEKS // 2
    out: list[MuscleTrend] = []
    for muscle, weekly in buckets.items():
        earlier = sum(weekly[:half]) / half
        recent = sum(weekly[half:]) / half
        # A tenth either way is noise, not a direction.
        if earlier == 0 and recent == 0:
            trend = "estable"
        elif recent > earlier * 1.15:
            trend = "sube"
        elif recent < earlier * 0.85:
            trend = "baja"
        else:
            trend = "estable"
        out.append(
            MuscleTrend(
                muscle=muscle, weekly=[round(v, 1) for v in weekly], trend=trend
            )
        )
    return out
