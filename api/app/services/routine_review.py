"""The routine assistant: read the routine, ask only what cannot be read.

The phase assessment asks seven questions because none of its answers live in
the database. This one is the opposite. The app already holds the whole routine,
every set ever logged, every substitution and the real training frequency, so
asking about any of that would be asking the user to repeat herself — and to
guess at numbers the app knows exactly.

So the five questions here are strictly the ones no amount of data can answer:
how often she *wants* to train (history says what happened, not what she meant),
how long a session may last, what she wants to emphasise, what hurts, and
whether she is chasing strength or size.

Everything else is measured, and every finding must name a specific change to a
specific exercise. "Your back volume is low" is not advice; "raise the lat
pulldown from 3 to 4 sets in Tirón" is. Findings that depend on history stay
silent until there is enough of it: an assistant that calls you stalled after
two sessions has not earned the right to an opinion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import (
    Exercise,
    ExercisePreference,
    Phase,
    RoutineDay,
    RoutineDayExercise,
    Session,
    SetLog,
)
from ..models.base import utcnow
from ..models.enums import Equipment, MovementPattern as P, SessionStatus
from . import muscles, routine_edit

# --- answer vocabularies -------------------------------------------------
DAYS_PER_WEEK = (2, 3, 4, 5, 6)
TIME_BUDGET = ("45", "60", "75", "90")
FOCUS = ("espalda", "pecho", "hombro", "gluteo", "cuadriceps", "brazos", "core", "nada")
AVOID = ("rodilla", "hombro", "espalda_baja", "nada")
GOAL = ("fuerza", "hipertrofia", "equilibrio")

# How demanding an exercise is. The seed's `default_rest_s` already encodes this
# deliberately — 45-60s for isolation, 90s for a secondary compound, 120-150s
# for a main lift — so it is a better signal than the movement pattern, which
# cannot tell a cable fly from a bench press (both `empuje_horizontal`).
ISOLATION_REST_S = 60
HEAVY_REST_S = 120

# Which patterns a complaint makes risky, and the kit that usually spares it.
# A machine fixes the path of the bar, so the joint is not asked to stabilise a
# load it is currently unhappy with.
AVOID_PATTERNS: dict[str, tuple[P, ...]] = {
    "rodilla": (P.cuadriceps,),
    "hombro": (P.empuje_vertical, P.empuje_horizontal),
    "espalda_baja": (P.cadena_posterior, P.cuadriceps),
}
GENTLER_EQUIPMENT = (Equipment.maquina, Equipment.polea)
RISKY_EQUIPMENT = (Equipment.barra,)

# Rep ranges by intent, for the first compound of a session (the one the session
# is really built around). Accessories are left alone: there is no single right
# rep range for a lateral raise and pretending otherwise is noise.
MAIN_RANGE = {"fuerza": (5, 8), "hipertrofia": (8, 12), "equilibrio": (6, 10)}

MIN_REST_COMPOUND_S = 90
SUGGESTED_REST_COMPOUND_S = 120
# Behavioural findings need this much history before they may speak.
MIN_SESSIONS_FOR_HABITS = 3
MIN_SESSIONS_FOR_STALL = 5
RECURRENT_SWAPS = 3
# A session may run this much over budget before it counts as too long: the
# estimate is not precise enough to quibble over five minutes.
TIME_TOLERANCE = 1.15
# Volume changes aim to land the muscle inside the productive band in one move
# rather than nibbling a set at a time — advice that takes four visits to say
# what it could have said once is bad advice. The caps keep a single exercise
# from absorbing the whole correction.
MAX_STEP_SETS = 2
MAX_SETS_PER_EXERCISE = 6
MIN_SETS_PER_EXERCISE = 2


@dataclass
class Action:
    """A change the assistant can make. `kind` decides which fields matter."""

    kind: str  # subir_series | bajar_series | anadir | quitar | sustituir
    #          | reordenar | cambiar_reps | cambiar_descanso
    rde_id: str | None = None
    day_id: str | None = None
    exercise_id: str | None = None
    exercise_name: str | None = None
    sets: int | None = None
    rep_min: int | None = None
    rep_max: int | None = None
    rest_s: int | None = None
    order: list[str] = field(default_factory=list)


@dataclass
class Finding:
    id: str
    kind: str  # key the UI turns into a sentence
    severity: str  # importante | mejorable | detalle
    # Numbers and names the sentence needs. The service never returns prose.
    detail: dict = field(default_factory=dict)
    action: Action | None = None


@dataclass
class ExerciseView:
    rde_id: str
    exercise_id: str
    name: str
    pattern: P
    equipment: Equipment
    per_side: bool
    order_index: int
    sets: int
    rep_min: int
    rep_max: int
    rest_s: int
    # The catalogue's own view of the exercise, kept apart from the routine's
    # override so the assistant can tell "this is a light movement" from "this
    # heavy movement has been given too little rest".
    default_rest_s: int
    rest_overridden: bool

    @property
    def isolation(self) -> bool:
        return self.default_rest_s <= ISOLATION_REST_S

    @property
    def heavy(self) -> bool:
        return self.default_rest_s >= HEAVY_REST_S


@dataclass
class DayView:
    day_id: str
    position: int
    name: str
    rows: list[ExerciseView]

    @property
    def total_sets(self) -> int:
        return sum(r.sets for r in self.rows)

    def minutes(self) -> int:
        return muscles.session_minutes(
            [(r.sets, r.rest_s, r.per_side) for r in self.rows]
        )


def load_routine(db: OrmSession, user_id: str) -> list[DayView]:
    """The active routine flattened into plain values, so every rule below reads
    the same snapshot and none of them re-query."""
    routine_id = routine_edit.active_routine_id(db, user_id)
    days = db.scalars(
        select(RoutineDay)
        .where(RoutineDay.routine_id == routine_id)
        .order_by(RoutineDay.position)
    ).all()
    out: list[DayView] = []
    for day in days:
        rows = db.execute(
            select(RoutineDayExercise, Exercise)
            .join(Exercise, Exercise.id == RoutineDayExercise.exercise_id)
            .where(RoutineDayExercise.routine_day_id == day.id)
            .order_by(RoutineDayExercise.order_index)
        ).all()
        out.append(
            DayView(
                day_id=day.id,
                position=day.position,
                name=day.name,
                rows=[
                    ExerciseView(
                        rde_id=rde.id,
                        exercise_id=ex.id,
                        name=ex.name,
                        pattern=ex.pattern,
                        equipment=ex.equipment,
                        per_side=ex.per_side,
                        order_index=rde.order_index,
                        sets=rde.target_sets,
                        rep_min=rde.rep_min,
                        rep_max=rde.rep_max,
                        rest_s=rde.rest_s or ex.default_rest_s,
                        default_rest_s=ex.default_rest_s,
                        rest_overridden=rde.rest_s is not None,
                    )
                    for rde, ex in rows
                ],
            )
        )
    return out


def sets_by_pattern(days: list[DayView]) -> dict[P, float]:
    totals: dict[P, float] = {}
    for day in days:
        for row in day.rows:
            totals[row.pattern] = totals.get(row.pattern, 0) + row.sets
    return totals


def _answer(answers: dict, key: str, allowed, default):
    value = answers.get(key)
    return value if value in allowed else default


def _focus_muscles(answers: dict) -> set[str]:
    """`brazos` is the one answer that is not already a muscle key."""
    raw = answers.get("prioridad") or []
    if isinstance(raw, str):
        raw = [raw]
    chosen: set[str] = set()
    for value in raw:
        if value == "brazos":
            chosen.update({"biceps", "triceps"})
        elif value in muscles.MUSCLES:
            chosen.add(value)
    return chosen


# --- structural findings -------------------------------------------------


def _step_sets(
    weekly_now: float, weekly_goal: float, weeks: float, sets_now: int, *, up: bool
) -> int:
    """Sets this exercise should carry to move the muscle to where it belongs.

    Working in weekly terms and converting back means one proposal does the job
    the band needs, instead of a +1 that leaves the muscle exactly as short as
    it was and invites the same advice next week.
    """
    import math

    gap_weekly = (weekly_goal - weekly_now) if up else (weekly_now - weekly_goal)
    if gap_weekly <= 0:
        return sets_now
    step = min(MAX_STEP_SETS, max(1, math.ceil(gap_weekly * weeks)))
    if up:
        return min(sets_now + step, MAX_SETS_PER_EXERCISE)
    return max(sets_now - step, MIN_SETS_PER_EXERCISE)


def _volume_findings(
    days: list[DayView],
    volumes: list[muscles.MuscleVolume],
    focus: set[str],
    over_budget: frozenset[str],
    weeks: float,
) -> list[Finding]:
    out: list[Finding] = []
    for vol in volumes:
        prioritised = vol.muscle in focus
        if vol.band == "efectivo" or (vol.band == "justo" and not prioritised):
            continue
        if vol.band == "alto":
            row, day = _biggest_contributor(days, vol.muscle)
            if row is None or row.sets <= MIN_SETS_PER_EXERCISE:
                continue
            target = _step_sets(vol.weekly_sets, muscles.GOOD_MAX, weeks, row.sets, up=False)
            if target == row.sets:
                continue
            out.append(
                Finding(
                    id=f"volumen_alto:{vol.muscle}",
                    kind="volumen_alto",
                    severity="mejorable",
                    detail={
                        "muscle": vol.muscle,
                        "weekly": vol.weekly_sets,
                        "exercise": row.name,
                        "day": day.name,
                        "from": row.sets,
                        "to": target,
                    },
                    action=Action(
                        kind="bajar_series", rde_id=row.rde_id, sets=target
                    ),
                )
            )
            continue

        # Low, or merely adequate for a muscle she asked to emphasise. Only look
        # in sessions that still have room on the clock.
        row, day = _biggest_contributor(days, vol.muscle, skip_days=over_budget)
        if row is None and _biggest_contributor(days, vol.muscle)[0] is not None:
            # It exists, but only in sessions that already run long. Say nothing
            # here: the session-too-long finding is the one to act on first.
            continue
        kind = "volumen_prioridad" if prioritised and vol.band == "justo" else "volumen_bajo"
        if row is not None:
            goal_weekly = muscles.GOOD_MIN if prioritised else muscles.LOW
            target = _step_sets(vol.weekly_sets, goal_weekly, weeks, row.sets, up=True)
            if target == row.sets:
                continue
            out.append(
                Finding(
                    id=f"{kind}:{vol.muscle}",
                    kind=kind,
                    severity="importante" if vol.band == "bajo" else "mejorable",
                    detail={
                        "muscle": vol.muscle,
                        "weekly": vol.weekly_sets,
                        "exercise": row.name,
                        "day": day.name,
                        "from": row.sets,
                        "to": target,
                    },
                    action=Action(
                        kind="subir_series", rde_id=row.rde_id, sets=target
                    ),
                )
            )
        else:
            out.append(
                Finding(
                    id=f"volumen_ausente:{vol.muscle}",
                    kind="volumen_ausente",
                    severity="importante",
                    detail={"muscle": vol.muscle, "weekly": vol.weekly_sets},
                )
            )
    return out


def _trains(row: ExerciseView, muscles_set: set[str]) -> bool:
    """Whether this exercise does *direct* work for any of those muscles."""
    return any(
        row.pattern in muscles.DIRECT_PATTERNS.get(m, ()) for m in muscles_set
    )


def _biggest_contributor(
    days: list[DayView], muscle: str, skip_days: frozenset[str] = frozenset()
) -> tuple[ExerciseView | None, DayView | None]:
    """The exercise doing most of the direct work for a muscle — the one to move
    when that muscle needs more or less.

    `skip_days` excludes sessions that already run over the time budget: adding
    a set to a session that does not fit is not a fix, it is a second problem.
    """
    patterns = set(muscles.DIRECT_PATTERNS.get(muscle, ()))
    best: tuple[ExerciseView, DayView] | None = None
    for day in days:
        if day.day_id in skip_days:
            continue
        for row in day.rows:
            if row.pattern not in patterns:
                continue
            if best is None or row.sets > best[0].sets:
                best = (row, day)
    return best if best else (None, None)


def _time_findings(
    days: list[DayView], budget_min: int, protected: set[str]
) -> list[Finding]:
    out: list[Finding] = []
    for day in days:
        minutes = day.minutes()
        if minutes <= budget_min * TIME_TOLERANCE:
            continue
        # Trim the accessory with the most sets: the last thing in a session is
        # the first thing to give when the clock runs out. Never trim a muscle
        # this same review is asking her to train more — advice that contradicts
        # itself is worse than no advice.
        candidates = [
            r
            for r in day.rows
            if r.isolation and r.sets > 2 and not _trains(r, protected)
        ]
        row = max(candidates, key=lambda r: r.sets) if candidates else None
        out.append(
            Finding(
                id=f"sesion_larga:{day.day_id}",
                kind="sesion_larga",
                severity="importante",
                detail={
                    "day": day.name,
                    "minutes": minutes,
                    "budget": budget_min,
                    "exercise": row.name if row else None,
                    "from": row.sets if row else None,
                    "to": row.sets - 1 if row else None,
                },
                action=(
                    Action(kind="bajar_series", rde_id=row.rde_id, sets=row.sets - 1)
                    if row
                    else None
                ),
            )
        )
    return out


def _order_findings(days: list[DayView]) -> list[Finding]:
    out: list[Finding] = []
    for day in days:
        rows = day.rows
        misplaced = any(
            rows[i].isolation and not rows[j].isolation
            for i in range(len(rows))
            for j in range(i + 1, len(rows))
        )
        if not misplaced:
            continue
        # Stable partition: compounds keep their relative order, then isolation.
        ordered = [r for r in rows if not r.isolation] + [
            r for r in rows if r.isolation
        ]
        out.append(
            Finding(
                id=f"orden:{day.day_id}",
                kind="orden",
                severity="mejorable",
                detail={
                    "day": day.name,
                    "first": next((r.name for r in rows if r.isolation), None),
                },
                action=Action(
                    kind="reordenar",
                    day_id=day.day_id,
                    order=[r.rde_id for r in ordered],
                ),
            )
        )
    return out


def _rep_findings(days: list[DayView], goal: str) -> list[Finding]:
    lo, hi = MAIN_RANGE[goal]
    out: list[Finding] = []
    for day in days:
        main = next((r for r in day.rows if not r.isolation), None)
        if main is None:
            continue
        # Only when the range is nowhere near the intent. A well-built plan mixes
        # heavy and lighter days on purpose — flagging a hypertrophy session for
        # not being a strength session would be the app misreading good design.
        if not (main.rep_min > hi + 3 or main.rep_max < lo - 2):
            continue
        out.append(
            Finding(
                id=f"reps:{main.rde_id}",
                kind="reps",
                severity="mejorable",
                detail={
                    "day": day.name,
                    "exercise": main.name,
                    "goal": goal,
                    "from_min": main.rep_min,
                    "from_max": main.rep_max,
                    "to_min": lo,
                    "to_max": hi,
                },
                action=Action(
                    kind="cambiar_reps", rde_id=main.rde_id, rep_min=lo, rep_max=hi
                ),
            )
        )
    return out


def _rest_findings(days: list[DayView]) -> list[Finding]:
    """Only where the routine overrides the catalogue downward on a heavy lift.
    A cable fly resting 60s is not a mistake, it is what a cable fly needs, and
    saying otherwise would be the app second-guessing its own data."""
    out: list[Finding] = []
    for day in days:
        for row in day.rows:
            if not (row.heavy and row.rest_overridden and row.rest_s < MIN_REST_COMPOUND_S):
                continue
            out.append(
                Finding(
                    id=f"descanso:{row.rde_id}",
                    kind="descanso",
                    severity="detalle",
                    detail={
                        "day": day.name,
                        "exercise": row.name,
                        "from": row.rest_s,
                        "to": SUGGESTED_REST_COMPOUND_S,
                    },
                    action=Action(
                        kind="cambiar_descanso",
                        rde_id=row.rde_id,
                        rest_s=SUGGESTED_REST_COMPOUND_S,
                    ),
                )
            )
    return out


def _swap_detail(row: ExerciseView, swap: Exercise) -> dict:
    """The facts a comparison needs: which two exercises, and what differs.

    The pattern is always shared — that is what makes them interchangeable — so
    the honest headline of any swap is that the movement stays and the tool
    changes.
    """
    return {
        "from_id": row.exercise_id,
        "to_id": swap.id,
        "pattern": row.pattern.value,
        "from_equipment": row.equipment.value,
        "to_equipment": swap.equipment.value,
        "from_rest_s": row.default_rest_s,
        "to_rest_s": swap.default_rest_s,
    }


def _gentler_alternative(db: OrmSession, row: ExerciseView) -> Exercise | None:
    """A guided version of the same movement, of comparable demand.

    Comparable demand is the part that matters. Swapping a squat for a leg
    extension would trade one knee problem for a worse one and quietly delete a
    compound from the routine, so candidates must sit in the same weight class:
    a main lift is only ever replaced by another main lift.
    """
    candidates = db.scalars(
        select(Exercise).where(
            Exercise.pattern == row.pattern,
            Exercise.equipment.in_(GENTLER_EQUIPMENT),
            Exercise.id != row.exercise_id,
        )
    ).all()
    same_class = [
        c
        for c in candidates
        if (c.default_rest_s <= ISOLATION_REST_S) == row.isolation
    ]
    if not same_class:
        return None
    # Closest in demand first, then a stable name order.
    return min(
        same_class, key=lambda c: (abs(c.default_rest_s - row.default_rest_s), c.name)
    )


def _avoid_findings(
    db: OrmSession, days: list[DayView], avoid: str
) -> list[Finding]:
    """Something hurts. Keep the movement, change the tool: same pattern, but on
    a machine that fixes the path instead of a free bar that does not."""
    if avoid == "nada":
        return []
    patterns = AVOID_PATTERNS.get(avoid, ())
    out: list[Finding] = []
    for day in days:
        for row in day.rows:
            if row.pattern not in patterns or row.equipment not in RISKY_EQUIPMENT:
                continue
            swap = _gentler_alternative(db, row)
            if swap is None:
                continue
            out.append(
                Finding(
                    id=f"molestia:{row.rde_id}",
                    kind="molestia",
                    severity="importante",
                    detail={
                        "day": day.name,
                        "exercise": row.name,
                        "avoid": avoid,
                        "replacement": swap.name,
                        # Enough for the UI to show both exercises side by side
                        # and say what actually differs. A swap the user cannot
                        # inspect is one she has to take on trust.
                        **_swap_detail(row, swap),
                    },
                    action=Action(
                        kind="sustituir",
                        rde_id=row.rde_id,
                        exercise_id=swap.id,
                        exercise_name=swap.name,
                    ),
                )
            )
    return out


# --- behavioural findings ------------------------------------------------


def _completed_sessions(db: OrmSession, user_id: str) -> int:
    return (
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


def _swap_findings(db: OrmSession, user_id: str, days: list[DayView]) -> list[Finding]:
    """A swap made again and again is not an exception, it is the routine being
    wrong on paper."""
    rows = db.execute(
        select(
            ExercisePreference.planned_exercise_id,
            ExercisePreference.substitution_count,
            Exercise,
        )
        .join(Exercise, Exercise.id == ExercisePreference.preferred_exercise_id)
        .where(
            ExercisePreference.user_id == user_id,
            ExercisePreference.substitution_count >= RECURRENT_SWAPS,
        )
    ).all()
    by_planned = {r[0]: r for r in rows}
    out: list[Finding] = []
    for day in days:
        for row in day.rows:
            hit = by_planned.get(row.exercise_id)
            if hit is None:
                continue
            _, count, preferred = hit
            out.append(
                Finding(
                    id=f"sustitucion:{row.rde_id}",
                    kind="sustitucion",
                    severity="mejorable",
                    detail={
                        "day": day.name,
                        "exercise": row.name,
                        "replacement": preferred.name,
                        "count": count,
                        **_swap_detail(row, preferred),
                    },
                    action=Action(
                        kind="sustituir",
                        rde_id=row.rde_id,
                        exercise_id=preferred.id,
                        exercise_name=preferred.name,
                    ),
                )
            )
    return out


def _never_logged_findings(
    db: OrmSession, user_id: str, days: list[DayView]
) -> list[Finding]:
    """In the routine but never once performed. Either it is always skipped or
    the machine is never free; both mean the plan is not what happens."""
    done_per_day = dict(
        db.execute(
            select(Session.routine_day_id, func.count())
            .where(
                Session.user_id == user_id,
                Session.status == SessionStatus.completed,
            )
            .group_by(Session.routine_day_id)
        ).all()
    )
    logged = set(
        db.scalars(
            select(SetLog.exercise_id)
            .join(Session, Session.id == SetLog.session_id)
            .where(Session.user_id == user_id, SetLog.voided.is_(False))
        ).all()
    )
    out: list[Finding] = []
    for day in days:
        if done_per_day.get(day.day_id, 0) < MIN_SESSIONS_FOR_HABITS:
            continue
        for row in day.rows:
            if row.exercise_id in logged:
                continue
            out.append(
                Finding(
                    id=f"nunca:{row.rde_id}",
                    kind="nunca_registrado",
                    severity="mejorable",
                    detail={
                        "day": day.name,
                        "exercise": row.name,
                        "sessions": done_per_day.get(day.day_id, 0),
                    },
                    action=Action(kind="quitar", rde_id=row.rde_id),
                )
            )
    return out


def _in_deficit(db: OrmSession, user_id: str) -> bool:
    """During a cut the app deliberately stops pushing load (progression.py), so
    flat numbers are the plan working, not a problem."""
    from ..models.phase import PhaseKind

    phase = db.scalars(
        select(Phase).where(Phase.user_id == user_id, Phase.ended_on.is_(None))
    ).first()
    return phase is not None and phase.kind == PhaseKind.definicion


def _stall_findings(
    db: OrmSession, user_id: str, days: list[DayView], goal: str
) -> list[Finding]:
    if _in_deficit(db, user_id):
        return []
    out: list[Finding] = []
    for day in days:
        for row in day.rows:
            history = db.execute(
                select(Session.started_at, SetLog.weight_kg, SetLog.reps)
                .join(Session, Session.id == SetLog.session_id)
                .where(
                    Session.user_id == user_id,
                    SetLog.exercise_id == row.exercise_id,
                    SetLog.voided.is_(False),
                )
                .order_by(Session.started_at)
            ).all()
            best_per_session: dict = {}
            for started, weight, reps in history:
                key = started.date()
                one_rm = float(weight) * (1 + reps / 30)
                best_per_session[key] = max(best_per_session.get(key, 0), one_rm)
            if len(best_per_session) < MIN_SESSIONS_FOR_STALL:
                continue
            values = [best_per_session[k] for k in sorted(best_per_session)]
            recent, earlier = values[-4:], max(values[:-4])
            if max(recent) > earlier:
                continue
            # Same intent, more room to move: a wider range lets her add reps
            # before she has to add weight.
            lo, hi = MAIN_RANGE[goal]
            out.append(
                Finding(
                    id=f"estancado:{row.rde_id}",
                    kind="estancado",
                    severity="mejorable",
                    detail={
                        "day": day.name,
                        "exercise": row.name,
                        "sessions": len(values),
                        "to_min": lo,
                        "to_max": hi + 2,
                    },
                    action=Action(
                        kind="cambiar_reps",
                        rde_id=row.rde_id,
                        rep_min=lo,
                        rep_max=hi + 2,
                    ),
                )
            )
    return out


def _frequency_finding(
    db: OrmSession, user_id: str, wanted: int
) -> list[Finding]:
    """What she does versus what she meant to do. No action: the routine is not
    what is wrong here, and pretending otherwise would be presumptuous."""
    since = utcnow() - timedelta(weeks=8)
    done = (
        db.scalar(
            select(func.count())
            .select_from(Session)
            .where(
                Session.user_id == user_id,
                Session.status == SessionStatus.completed,
                Session.started_at >= since,
            )
        )
        or 0
    )
    first = db.scalar(
        select(func.min(Session.started_at)).where(
            Session.user_id == user_id, Session.started_at >= since
        )
    )
    if first is None:
        return []
    weeks = max((utcnow() - first).days / 7, 1.0)
    if weeks < 3:  # too short a window to draw a line through
        return []
    real = done / weeks
    if real >= wanted - 0.75:
        return []
    return [
        Finding(
            id="frecuencia",
            kind="frecuencia",
            severity="detalle",
            detail={"real": round(real, 1), "wanted": wanted},
        )
    ]


# --- entry point ---------------------------------------------------------

SEVERITY_ORDER = {"importante": 0, "mejorable": 1, "detalle": 2}


def _resolve(findings: list[Finding]) -> list[Finding]:
    """Drop advice that reads as nonsense next to other advice.

    Proposing to remove an exercise *and* to give it two more sets is not
    dangerous — the edits touch different columns — but a person reading both
    would rightly stop trusting the assistant. Removal is the stronger claim, so
    it wins and the rest go quiet.
    """
    removing = {
        f.action.rde_id
        for f in findings
        if f.action and f.action.kind == "quitar" and f.action.rde_id
    }
    if not removing:
        return findings
    return [
        f
        for f in findings
        if not (
            f.action
            and f.action.kind != "quitar"
            and f.action.rde_id in removing
        )
    ]


@dataclass
class Review:
    days_per_week: int
    volumes: list[muscles.MuscleVolume]
    session_minutes: list[tuple[str, int]]
    findings: list[Finding]
    # Set when the answers imply a different number of sessions than the routine
    # has; filled in by the restructure engine.
    restructure: object | None = None


def review(db: OrmSession, user_id: str, answers: dict) -> Review:
    days = load_routine(db, user_id)
    days_per_week = _answer(answers, "dias", DAYS_PER_WEEK, 4)
    if isinstance(days_per_week, str):
        days_per_week = int(days_per_week)
    budget = int(_answer(answers, "tiempo", TIME_BUDGET, "60"))
    goal = _answer(answers, "objetivo", GOAL, "equilibrio")
    avoid = _answer(answers, "evitar", AVOID, "nada")
    focus = _focus_muscles(answers)

    volumes = muscles.weekly_volume(sets_by_pattern(days), len(days), days_per_week)

    # Worked out before any finding is written, because two rules that disagree
    # about the same exercise would each be defensible alone and useless
    # together: never trim what we are asking her to grow, and never grow a
    # session that already does not fit.
    protected = {v.muscle for v in volumes if v.band == "bajo"} | focus
    over_budget = frozenset(
        d.day_id for d in days if d.minutes() > budget * TIME_TOLERANCE
    )

    findings: list[Finding] = []
    findings += _avoid_findings(db, days, avoid)
    findings += _volume_findings(
        days,
        volumes,
        focus,
        over_budget,
        muscles.weeks_per_cycle(len(days), days_per_week),
    )
    findings += _time_findings(days, budget, protected)
    findings += _order_findings(days)
    findings += _rep_findings(days, goal)
    findings += _rest_findings(days)

    if _completed_sessions(db, user_id) >= MIN_SESSIONS_FOR_HABITS:
        findings += _swap_findings(db, user_id, days)
        findings += _never_logged_findings(db, user_id, days)
        findings += _stall_findings(db, user_id, days, goal)
        findings += _frequency_finding(db, user_id, days_per_week)

    findings = _resolve(findings)
    findings.sort(key=lambda f: SEVERITY_ORDER[f.severity])
    return Review(
        days_per_week=days_per_week,
        volumes=volumes,
        session_minutes=[(d.name, d.minutes()) for d in days],
        findings=findings,
    )
