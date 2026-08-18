"""Redistributing a routine across a different number of training days.

The wheel (spec §5.1) does not need the number of sessions to match the number
of days trained: five sessions at three a week simply takes 1.67 weeks to come
round. That is harmless for the pointer but not for the training — every muscle
then gets worked once every twelve days, and weekly volume falls by 40% without
anyone deciding it should.

So when the user says she trains three days, the work is not thrown away, it is
repacked: the same exercises, the same sets, dealt into three sessions instead
of five. That keeps the weekly volume she had and raises the frequency.

It also makes the sessions longer, and that is the part this module refuses to
hide. It estimates the clock, and if the sessions do not fit the time she said
she has, it trims — from the muscles with the most room to spare, never from
the ones already short — and reports every set it removed. If it still does not
fit after trimming, it says so instead of quietly shipping a plan she cannot
finish.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..models.enums import MovementPattern as P
from . import muscles
from .routine_review import ISOLATION_REST_S, DayView, ExerciseView

PUSH = {P.empuje_horizontal, P.empuje_vertical, P.deltoides_lateral, P.triceps}
PULL = {P.tiron_horizontal, P.tiron_vertical, P.biceps}
LOWER = {P.cuadriceps, P.cadena_posterior, P.gluteo, P.gemelo, P.abduccion}
CORE = {P.core}
UPPER = PUSH | PULL
ALL = UPPER | LOWER | CORE

# What each session may contain, by how many days a week she trains. The shapes
# are the conventional ones, chosen so every muscle is hit at least twice a
# week: that frequency, not the split's name, is what makes a week work.
TEMPLATES: dict[int, list[tuple[str, set]]] = {
    2: [("Cuerpo completo A", ALL), ("Cuerpo completo B", ALL)],
    3: [
        ("Cuerpo completo A", ALL),
        ("Cuerpo completo B", ALL),
        ("Cuerpo completo C", ALL),
    ],
    4: [
        ("Torso A", UPPER | CORE),
        ("Pierna A", LOWER | CORE),
        ("Torso B", UPPER | CORE),
        ("Pierna B", LOWER | CORE),
    ],
    5: [
        ("Torso", UPPER | CORE),
        ("Pierna", LOWER | CORE),
        ("Empuje", PUSH),
        ("Tirón", PULL),
        ("Pierna (hipertrofia)", LOWER | CORE),
    ],
    6: [
        ("Empuje A", PUSH),
        ("Tirón A", PULL),
        ("Pierna A", LOWER | CORE),
        ("Empuje B", PUSH),
        ("Tirón B", PULL),
        ("Pierna B", LOWER | CORE),
    ],
}

# Never cut a working exercise below this, and never take a muscle below LOW:
# a plan that fits the clock by making the training pointless is not a fix.
MIN_SETS = 2


@dataclass
class NewExercise:
    exercise_id: str
    name: str
    pattern: P
    sets: int
    rep_min: int
    rep_max: int
    rest_s: int
    per_side: bool
    default_rest_s: int

    @property
    def isolation(self) -> bool:
        return self.default_rest_s <= ISOLATION_REST_S


@dataclass
class NewSession:
    name: str
    rows: list[NewExercise] = field(default_factory=list)

    @property
    def total_sets(self) -> int:
        return sum(r.sets for r in self.rows)

    def minutes(self) -> int:
        return muscles.session_minutes(
            [(r.sets, r.rest_s, r.per_side) for r in self.rows]
        )


@dataclass
class Restructure:
    days_per_week: int
    sessions: list[NewSession]
    # Sets removed to fit the clock: [{exercise, muscle, from, to}]
    trimmed: list[dict] = field(default_factory=list)
    # True when every session fits the stated budget after trimming.
    fits: bool = True
    # Muscles left under the productive band by the trimming, if any.
    under_target: list[str] = field(default_factory=list)
    sets_before: int = 0
    sets_after: int = 0


def _flatten(days: list[DayView]) -> list[ExerciseView]:
    return [row for day in days for row in day.rows]


def _eligible(session_patterns: set, pattern: P) -> bool:
    return pattern in session_patterns


def distribute(days: list[DayView], days_per_week: int) -> list[NewSession]:
    """Deal every exercise into the new sessions, keeping its sets and reps.

    Heaviest first, each one going to the eligible session with least work so
    far: that balances the sessions without needing to know anything about the
    exercises beyond what the catalogue already says.
    """
    template = TEMPLATES[days_per_week]
    sessions = [NewSession(name=name) for name, _ in template]
    patterns = [pats for _, pats in template]

    rows = sorted(
        _flatten(days), key=lambda r: (r.default_rest_s, r.sets), reverse=True
    )
    for row in rows:
        candidates = [
            i for i, pats in enumerate(patterns) if _eligible(pats, row.pattern)
        ]
        if not candidates:  # pattern outside every session: keep it, don't drop it
            candidates = list(range(len(sessions)))
        target = min(candidates, key=lambda i: (sessions[i].total_sets, i))
        sessions[target].rows.append(
            NewExercise(
                exercise_id=row.exercise_id,
                name=row.name,
                pattern=row.pattern,
                sets=row.sets,
                rep_min=row.rep_min,
                rep_max=row.rep_max,
                rest_s=row.rest_s,
                per_side=row.per_side,
                default_rest_s=row.default_rest_s,
            )
        )

    # Compounds first, heaviest first; isolation last. Same rule the review
    # applies to the existing routine, so both agree on what good order means.
    for session in sessions:
        session.rows.sort(key=lambda r: (r.isolation, -r.default_rest_s, r.name))
    return sessions


def _weekly_by_muscle(sessions: list[NewSession], days_per_week: int) -> dict:
    by_pattern: dict = {}
    for session in sessions:
        for row in session.rows:
            by_pattern[row.pattern] = by_pattern.get(row.pattern, 0) + row.sets
    return {
        v.muscle: v.weekly_sets
        for v in muscles.weekly_volume(by_pattern, len(sessions), days_per_week)
    }


def _surplus(weekly: dict, row: NewExercise) -> float:
    """How much room the muscles this exercise trains have above the productive
    floor. Trimming takes from whoever has the most to spare."""
    contributions = muscles.CONTRIBUTION.get(row.pattern, {})
    if not contributions:
        return 0.0
    return min(weekly.get(m, 0.0) - muscles.GOOD_MIN for m in contributions)


def trim_to_budget(
    sessions: list[NewSession], days_per_week: int, budget_min: int
) -> tuple[list[dict], bool]:
    """Remove sets until the sessions fit, taking from the muscles with the most
    slack. Returns what was removed and whether it ended up fitting."""
    removed: list[dict] = []
    guard = 0
    while guard < 500:
        guard += 1
        over = [s for s in sessions if s.minutes() > budget_min]
        if not over:
            return removed, True
        session = max(over, key=lambda s: s.minutes())
        weekly = _weekly_by_muscle(sessions, days_per_week)
        candidates = [
            r
            for r in session.rows
            if r.sets > MIN_SETS and _surplus(weekly, r) > 0
        ]
        if not candidates:
            # Everything left is either at the floor or already short. Stop and
            # say it does not fit rather than gut the training to beat a clock.
            return removed, False
        row = max(candidates, key=lambda r: (_surplus(weekly, r), r.sets))
        row.sets -= 1
        removed.append(
            {
                "exercise": row.name,
                "session": session.name,
                "from": row.sets + 1,
                "to": row.sets,
            }
        )
    return removed, False


def restructure(
    days: list[DayView], days_per_week: int, budget_min: int
) -> Restructure | None:
    """None when the routine already has the right shape — there is nothing to
    propose and saying so is better than inventing a change."""
    if days_per_week not in TEMPLATES or days_per_week == len(days):
        return None

    sets_before = sum(r.sets for r in _flatten(days))
    sessions = distribute(days, days_per_week)
    # Measured before trimming so `under_target` reports what the clock cost her,
    # not muscles that were already short — those are the review's business, and
    # blaming the restructure for them would misread the cause.
    before = _weekly_by_muscle(sessions, days_per_week)
    trimmed, fits = trim_to_budget(sessions, days_per_week, budget_min)
    after = _weekly_by_muscle(sessions, days_per_week)
    return Restructure(
        days_per_week=days_per_week,
        sessions=sessions,
        trimmed=trimmed,
        fits=fits,
        under_target=[
            m
            for m in after
            if before[m] >= muscles.GOOD_MIN and after[m] < muscles.GOOD_MIN
        ],
        sets_before=sets_before,
        sets_after=sum(s.total_sets for s in sessions),
    )
