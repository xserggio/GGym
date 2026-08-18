"""From movement patterns to muscle groups, and from a routine to weekly volume.

Substitutions reason about *patterns* (spec §5.3) because that is what makes two
exercises interchangeable. Volume cannot: a set of bench press trains the chest
directly and the triceps as well, and counting patterns alone would say this
user does three sets of triceps a week when she really does eleven. Advice built
on that count would be wrong in a way that sounds precise, so the mapping below
carries both the direct work and the indirect share.

The weights are deliberately coarse — 1.0 direct, 0.5 for a muscle that works
hard as a synergist, 0.3 for one that only assists. Nothing here is measured;
they are the ratios coaches use, and their only job is to keep the app from
raising alarms about muscles that are already well covered.

Sets per *week* is the number the guidelines are written in, so per-cycle volume
is converted using how often the user actually trains: the same routine is a
very different stimulus at five sessions a week than at three.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..models.enums import MovementPattern as P

# Display order: torso pushing, torso pulling, arms, legs, the rest.
MUSCLES = (
    "pecho",
    "espalda",
    "hombro",
    "biceps",
    "triceps",
    "cuadriceps",
    "isquios",
    "gluteo",
    "gemelo",
    "core",
)

CONTRIBUTION: dict[P, dict[str, float]] = {
    P.empuje_horizontal: {"pecho": 1.0, "triceps": 0.5, "hombro": 0.5},
    P.empuje_vertical: {"hombro": 1.0, "triceps": 0.5, "pecho": 0.3},
    P.tiron_horizontal: {"espalda": 1.0, "biceps": 0.5},
    P.tiron_vertical: {"espalda": 1.0, "biceps": 0.5},
    P.deltoides_lateral: {"hombro": 1.0},
    P.triceps: {"triceps": 1.0},
    P.biceps: {"biceps": 1.0},
    P.cuadriceps: {"cuadriceps": 1.0, "gluteo": 0.3},
    P.cadena_posterior: {"isquios": 1.0, "gluteo": 0.5},
    P.gluteo: {"gluteo": 1.0, "isquios": 0.3},
    P.gemelo: {"gemelo": 1.0},
    P.core: {"core": 1.0},
    P.abduccion: {"gluteo": 0.5},
}

# Which patterns actually train a group directly. Used when proposing *where* to
# add volume: you raise chest work with a press, not with a lateral raise.
DIRECT_PATTERNS: dict[str, tuple[P, ...]] = {
    "pecho": (P.empuje_horizontal,),
    "espalda": (P.tiron_horizontal, P.tiron_vertical),
    "hombro": (P.empuje_vertical, P.deltoides_lateral),
    "biceps": (P.biceps,),
    "triceps": (P.triceps,),
    "cuadriceps": (P.cuadriceps,),
    "isquios": (P.cadena_posterior,),
    "gluteo": (P.gluteo,),
    "gemelo": (P.gemelo,),
    "core": (P.core,),
}

# Weekly effective sets. Below LOW a muscle is not being trained enough to grow
# or hold; above HIGH the extra sets mostly cost recovery. The band between
# GOOD_MIN and GOOD_MAX is where the guidelines put productive work — inside it
# the app says nothing, because there is nothing to fix.
LOW = 6.0
GOOD_MIN = 10.0
GOOD_MAX = 20.0
HIGH = 22.0

# Rough clock: a working set plus its rest. Per-side exercises are performed
# twice, so they cost twice the work time (not twice the rest).
SET_WORK_S = 45
WARMUP_S = 300


@dataclass
class MuscleVolume:
    muscle: str
    weekly_sets: float
    # "bajo" | "justo" | "efectivo" | "alto" — a key the UI translates.
    band: str


def band_for(weekly: float) -> str:
    if weekly < LOW:
        return "bajo"
    if weekly < GOOD_MIN:
        return "justo"
    if weekly <= GOOD_MAX:
        return "efectivo"
    return "alto" if weekly > HIGH else "efectivo"


def weeks_per_cycle(sessions_in_cycle: int, days_per_week: int) -> float:
    """How long one turn of the wheel takes. The wheel does not care about the
    calendar (spec §5.1): five sessions at three a week is a 1.67-week cycle."""
    if days_per_week <= 0 or sessions_in_cycle <= 0:
        return 1.0
    return sessions_in_cycle / days_per_week


def weekly_volume(
    sets_by_pattern: dict[P, float], sessions_in_cycle: int, days_per_week: int
) -> list[MuscleVolume]:
    """Effective weekly sets per muscle, ordered as MUSCLES."""
    weeks = weeks_per_cycle(sessions_in_cycle, days_per_week)
    totals = dict.fromkeys(MUSCLES, 0.0)
    for pattern, sets in sets_by_pattern.items():
        for muscle, weight in CONTRIBUTION.get(pattern, {}).items():
            totals[muscle] += sets * weight
    return [
        MuscleVolume(
            muscle=m,
            weekly_sets=round(totals[m] / weeks, 1),
            band=band_for(totals[m] / weeks),
        )
        for m in MUSCLES
    ]


def session_minutes(rows: list[tuple[int, int, bool]]) -> int:
    """Estimated minutes for one session from (sets, rest_s, per_side) rows.

    Deliberately includes a fixed warm-up and counts per-side work twice: an
    estimate that quietly runs short is worse than none, because the whole point
    is telling someone whether their session fits in the time they have.
    """
    total = WARMUP_S
    for sets, rest_s, per_side in rows:
        work = SET_WORK_S * (2 if per_side else 1)
        total += sets * (work + rest_s)
    return round(total / 60)
