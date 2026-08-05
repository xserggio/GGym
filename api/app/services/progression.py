"""Automatic progression (spec §5.2). On opening an exercise, prefill the weight
from the last session it was done. If every set that day reached rep_max, suggest
a bump: +5 kg for the lower-body patterns, +2,5 kg otherwise. Else repeat.

The rule and increments mirror the routine's `progression` block in the seed
(all_sets_at_rep_max, +2.5 upper / +5 lower)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..models import Exercise, RoutineDayExercise, Session, SetLog
from ..models.enums import MovementPattern
from ..schemas import Suggestion

LOWER_PATTERNS = {
    MovementPattern.cuadriceps,
    MovementPattern.cadena_posterior,
    MovementPattern.gluteo,
}
INCREMENT_UPPER_KG = 2.5
INCREMENT_LOWER_KG = 5.0


def _round_2_5(weight: float) -> float:
    return round(weight / 2.5) * 2.5


def suggestion(
    db: OrmSession,
    user_id: str,
    exercise_id: str,
    rep_max: int,
    pattern: MovementPattern,
    deload: bool = False,
) -> Suggestion:
    last_session_id = db.scalar(
        select(Session.id)
        .join(SetLog, SetLog.session_id == Session.id)
        .where(
            Session.user_id == user_id,
            SetLog.exercise_id == exercise_id,
            SetLog.voided.is_(False),
        )
        .order_by(Session.started_at.desc())
        .limit(1)
    )
    if last_session_id is None:
        return Suggestion(
            exercise_id=exercise_id,
            last_weight_kg=None,
            last_reps=[],
            all_at_rep_max=False,
            suggested_weight_kg=None,
            last_session_on=None,
        )

    logs = db.scalars(
        select(SetLog)
        .where(
            SetLog.session_id == last_session_id,
            SetLog.exercise_id == exercise_id,
            SetLog.voided.is_(False),
        )
        .order_by(SetLog.set_number)
    ).all()
    weights = [float(x.weight_kg) for x in logs]
    reps = [x.reps for x in logs]
    last_weight = max(weights) if weights else None
    all_at_rep_max = bool(reps) and all(r >= rep_max for r in reps)

    if deload and last_weight is not None:
        # Resuming after a break (spec §5.1): last weight −10%.
        suggested = _round_2_5(last_weight * 0.9)
    elif all_at_rep_max and last_weight is not None:
        increment = (
            INCREMENT_LOWER_KG if pattern in LOWER_PATTERNS else INCREMENT_UPPER_KG
        )
        suggested = round(last_weight + increment, 2)
    else:
        suggested = last_weight

    session = db.get(Session, last_session_id)
    on = None
    if session is not None:
        moment = session.ended_at or session.started_at
        on = moment.date()

    return Suggestion(
        exercise_id=exercise_id,
        last_weight_kg=last_weight,
        last_reps=reps,
        all_at_rep_max=all_at_rep_max,
        suggested_weight_kg=suggested,
        last_session_on=on,
    )


def suggestions_for_day(
    db: OrmSession, user_id: str, day_id: str, deload: bool = False
) -> list[Suggestion]:
    rows = db.execute(
        select(RoutineDayExercise, Exercise)
        .join(Exercise, Exercise.id == RoutineDayExercise.exercise_id)
        .where(RoutineDayExercise.routine_day_id == day_id)
        .order_by(RoutineDayExercise.order_index)
    ).all()
    return [
        suggestion(db, user_id, ex.id, rde.rep_max, ex.pattern, deload)
        for rde, ex in rows
    ]
