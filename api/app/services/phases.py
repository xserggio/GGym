"""Training phases: measure whether body weight is doing what the user intended.

The app has no intake data and never will, so it cannot drive a phase — diet
does that. What it can do honestly is compare the *outcome* against the declared
intent, which needs only the body-weight log we already keep, and adapt what it
expects from training. Nothing here produces a calorie target: the app's kcal
figure covers gym time alone, and dressing that up as a daily intake would be a
fabricated number with a confident face.

The guideline constants below are the opinionated part. They follow common
practice for lean gains and fat loss, and they are deliberately conservative:
the app caps what a user can ask of themselves rather than egging them on.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..models import BodyWeight, Phase, PhaseKind
from ..schemas import PhaseOut, PhaseStatus

# Intended weekly change as a percentage of body weight. A deficit beyond about
# 1%/week starts costing muscle; a surplus beyond ~0.5% mostly adds fat. The
# range is what the UI lets the user pick; DEFAULT is what it proposes.
LIMITS: dict[PhaseKind, tuple[float, float, float]] = {
    #                     min,   default, max
    PhaseKind.definicion: (-1.0, -0.5, -0.25),
    PhaseKind.superavit: (0.1, 0.25, 0.5),
    PhaseKind.mantenimiento: (0.0, 0.0, 0.0),
}

# How long a phase can reasonably run before the app suggests a change. A long
# deficit wears down adherence, sleep and training quality well before it stops
# working, so the nudge comes early and the warning not much later.
SUGGEST_END_WEEKS: dict[PhaseKind, int] = {
    PhaseKind.definicion: 12,
    PhaseKind.superavit: 16,
    PhaseKind.mantenimiento: 0,  # no limit: maintenance is a resting state
}
HARD_LIMIT_WEEKS: dict[PhaseKind, int] = {
    PhaseKind.definicion: 16,
    PhaseKind.superavit: 24,
    PhaseKind.mantenimiento: 0,
}

# Body weight moves with water, food and the clock. Below this much history any
# "rate" is noise dressed as a trend, so the app says it does not know yet.
MIN_DAYS = 14
MIN_POINTS = 3
# Considered on target while within the larger of these two: a fixed floor for
# small targets, or a share of the target itself.
TOLERANCE_FLOOR_PCT = 0.15
TOLERANCE_SHARE = 0.4


@dataclass(frozen=True)
class Trend:
    rate_pct: float | None  # % of body weight per week
    points: int
    days: int


def clamp_rate(kind: PhaseKind, requested: float | None) -> float:
    """Keep the target inside the guideline range; the default when unset."""
    low, default, high = LIMITS[kind]
    if requested is None:
        return default
    return max(low, min(high, requested))


def _weights(db: OrmSession, user_id: str, since: date) -> list[tuple[date, float]]:
    rows = db.scalars(
        select(BodyWeight)
        .where(BodyWeight.user_id == user_id, BodyWeight.measured_on >= since)
        .order_by(BodyWeight.measured_on)
    ).all()
    return [(r.measured_on, float(r.weight_kg)) for r in rows]


def trend(db: OrmSession, user_id: str, since: date) -> Trend:
    """Least-squares slope of the weigh-ins, as % of body weight per week.

    Regression rather than first-versus-last: a single heavy or light morning at
    either end would otherwise swing the whole verdict.
    """
    points = _weights(db, user_id, since)
    if len(points) < MIN_POINTS:
        return Trend(None, len(points), 0)

    first = points[0][0]
    span = (points[-1][0] - first).days
    if span < MIN_DAYS:
        return Trend(None, len(points), span)

    xs = [(d - first).days for d, _ in points]
    ys = [w for _, w in points]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return Trend(None, n, span)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom

    kg_per_week = slope * 7
    return Trend(round(kg_per_week / mean_y * 100, 2), n, span)


def active(db: OrmSession, user_id: str) -> Phase | None:
    return db.scalar(
        select(Phase)
        .where(Phase.user_id == user_id, Phase.ended_on.is_(None))
        .order_by(Phase.started_on.desc())
    )


def _verdict(kind: PhaseKind, target: float, actual: float | None) -> str:
    """A key the UI translates; the service never returns display text."""
    if actual is None:
        return "sin_datos"
    tolerance = max(TOLERANCE_FLOOR_PCT, abs(target) * TOLERANCE_SHARE)
    diff = actual - target
    if abs(diff) <= tolerance:
        return "en_rumbo"
    if kind == PhaseKind.mantenimiento:
        return "subiendo" if diff > 0 else "bajando"
    # Signed against the direction of the goal: "fast" means past the target,
    # which in a deficit means losing quicker than intended.
    faster = diff < 0 if target < 0 else diff > 0
    return "demasiado_rapido" if faster else "demasiado_lento"


def status_for(db: OrmSession, user_id: str, phase: Phase, today: date | None = None) -> PhaseStatus:
    today = today or date.today()
    weeks = max(0, (today - phase.started_on).days) / 7
    t = trend(db, user_id, phase.started_on)

    suggest = SUGGEST_END_WEEKS[phase.kind]
    hard = HARD_LIMIT_WEEKS[phase.kind]
    duration = "ok"
    if hard and weeks >= hard:
        duration = "muy_larga"
    elif suggest and weeks >= suggest:
        duration = "larga"

    days_left = (phase.target_date - today).days if phase.target_date else None

    return PhaseStatus(
        weeks_elapsed=round(weeks, 1),
        measurements=t.points,
        actual_rate_pct=t.rate_pct,
        verdict=_verdict(phase.kind, phase.target_rate_pct, t.rate_pct),
        duration=duration,
        suggest_end_weeks=suggest or None,
        days_to_target=days_left,
    )


def out(db: OrmSession, user_id: str, phase: Phase) -> PhaseOut:
    return PhaseOut(
        id=phase.id,
        kind=phase.kind,
        started_on=phase.started_on,
        ended_on=phase.ended_on,
        target_rate_pct=phase.target_rate_pct,
        target_date=phase.target_date,
        target_weight_kg=phase.target_weight_kg,
        status=status_for(db, user_id, phase) if phase.ended_on is None else None,
    )


def start(
    db: OrmSession,
    user_id: str,
    kind: PhaseKind,
    target_rate_pct: float | None,
    target_date: date | None,
    target_weight_kg: float | None = None,
    today: date | None = None,
) -> Phase:
    """Open a phase, closing whatever was running. Phases are contiguous: there
    is always exactly one, or none at all."""
    today = today or date.today()
    if target_date is not None and target_date <= today:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "target date must be ahead")

    current = active(db, user_id)
    if current is not None:
        # A phase that ends the day it started would leave a zero-length record.
        current.ended_on = max(today, current.started_on)
        db.flush()

    phase = Phase(
        user_id=user_id,
        kind=kind,
        started_on=today,
        target_rate_pct=clamp_rate(kind, target_rate_pct),
        target_date=target_date,
        target_weight_kg=target_weight_kg,
    )
    db.add(phase)
    db.flush()
    return phase


def end(db: OrmSession, user_id: str, today: date | None = None) -> None:
    today = today or date.today()
    current = active(db, user_id)
    if current is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no active phase")
    current.ended_on = max(today, current.started_on)
    db.flush()


def history(db: OrmSession, user_id: str) -> list[Phase]:
    return list(
        db.scalars(
            select(Phase)
            .where(Phase.user_id == user_id)
            .order_by(Phase.started_on.desc())
        ).all()
    )


# --------------------------------------------------------------------------
# Advice: turning two questions and a date into a defensible number.
# --------------------------------------------------------------------------

# How fast muscle can actually be gained depends mostly on how long someone has
# been training: quick at the start, very slow after a few years, and pushing
# past that only adds fat.
SURPLUS_BY_TRAINING_AGE: dict[str, float] = {
    "menos_1": 0.40,
    "1_3": 0.25,
    "mas_3": 0.15,
}

# How fast fat can be lost depends mostly on how much there is. With plenty to
# lose the body draws on it happily; when already lean the same deficit starts
# taking muscle instead, so the rate has to come down.
DEFICIT_BY_FAT_LEVEL: dict[str, float] = {
    "alta": -0.90,
    "media": -0.60,
    "baja": -0.35,
}


def recommend(kind: PhaseKind, training_age: str | None, fat_level: str | None) -> tuple[float, str]:
    """Recommended rate and the key explaining why. Always inside LIMITS."""
    if kind == PhaseKind.mantenimiento:
        return 0.0, "mantenimiento"
    if kind == PhaseKind.superavit:
        band = training_age if training_age in SURPLUS_BY_TRAINING_AGE else "1_3"
        return clamp_rate(kind, SURPLUS_BY_TRAINING_AGE[band]), f"superavit_{band}"
    band = fat_level if fat_level in DEFICIT_BY_FAT_LEVEL else "media"
    return clamp_rate(kind, DEFICIT_BY_FAT_LEVEL[band]), f"definicion_{band}"


def current_weight(db: OrmSession, user_id: str) -> float | None:
    """Latest weigh-in. Used only as the base for arithmetic, never as a verdict:
    the trend is what judges a phase."""
    row = db.scalar(
        select(BodyWeight)
        .where(BodyWeight.user_id == user_id)
        .order_by(BodyWeight.measured_on.desc())
        .limit(1)
    )
    return float(row.weight_kg) if row else None


@dataclass(frozen=True)
class Feasibility:
    weeks: float
    required_rate_pct: float
    verdict: str  # viable | muy_exigente | direccion_contraria
    safe_rate_pct: float
    reachable_weight_kg: float | None
    weeks_needed: float | None


def feasibility(
    kind: PhaseKind,
    current_kg: float,
    target_kg: float,
    target_date: date,
    today: date | None = None,
) -> Feasibility | None:
    """Whether the date and the weight can both be true.

    Pure arithmetic, and the most useful thing the app can say about a target:
    a date on its own is a wish, but the rate it implies is checkable.
    """
    today = today or date.today()
    weeks = (target_date - today).days / 7
    if weeks <= 0 or current_kg <= 0:
        return None

    delta = target_kg - current_kg
    required = delta / current_kg * 100 / weeks

    low, _default, high = LIMITS[kind]
    # The most aggressive end of the guideline range for this direction.
    cap = low if kind == PhaseKind.definicion else high

    if kind != PhaseKind.mantenimiento and (
        (kind == PhaseKind.definicion and delta >= 0)
        or (kind == PhaseKind.superavit and delta <= 0)
    ):
        return Feasibility(round(weeks, 1), round(required, 2), "direccion_contraria", cap, None, None)

    if abs(required) <= abs(cap) + 1e-9:
        return Feasibility(round(weeks, 1), round(required, 2), "viable", cap, None, None)

    # Out of reach: say what *is* reachable by the date, and when the target
    # would arrive at a sane rate. Both are more useful than a refusal.
    reachable = current_kg * (1 + cap / 100 * weeks)
    weeks_needed = abs(delta / current_kg * 100 / cap)
    return Feasibility(
        round(weeks, 1),
        round(required, 2),
        "muy_exigente",
        cap,
        round(reachable, 1),
        round(weeks_needed, 1),
    )
