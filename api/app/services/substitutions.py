"""Substitutions ("máquina ocupada", spec §5.3).

Alternatives share the *movement pattern* of the planned exercise, ordered by
how often this user has already swapped to them.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session as OrmSession

from ..models import Exercise, ExercisePreference


def alternatives(
    db: OrmSession, user_id: str, exercise_id: str
) -> list[tuple[Exercise, int]]:
    base = db.get(Exercise, exercise_id)
    if base is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "exercise not found")

    count = func.coalesce(ExercisePreference.substitution_count, 0)
    rows = db.execute(
        select(Exercise, count)
        .outerjoin(
            ExercisePreference,
            and_(
                ExercisePreference.user_id == user_id,
                ExercisePreference.planned_exercise_id == exercise_id,
                ExercisePreference.preferred_exercise_id == Exercise.id,
            ),
        )
        .where(Exercise.pattern == base.pattern, Exercise.id != exercise_id)
        .order_by(desc(count), Exercise.name)
    ).all()
    return [(exercise, int(c)) for exercise, c in rows]


def record_substitution(
    db: OrmSession, user_id: str, planned_exercise_id: str, preferred_exercise_id: str
) -> None:
    """Increment the swap counter for a (planned -> preferred) pair. Callers must
    ensure this runs once per session substitution, not once per set."""
    pref = db.get(
        ExercisePreference, (user_id, planned_exercise_id, preferred_exercise_id)
    )
    if pref is None:
        db.add(
            ExercisePreference(
                user_id=user_id,
                planned_exercise_id=planned_exercise_id,
                preferred_exercise_id=preferred_exercise_id,
                substitution_count=1,
            )
        )
    else:
        pref.substitution_count += 1
