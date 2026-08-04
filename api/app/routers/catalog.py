from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..deps import get_current_user, get_db
from ..models import Exercise, User
from ..schemas import AlternativeOut, ExerciseOut
from ..services import substitutions

router = APIRouter(prefix="/exercises", tags=["catalogue"])


@router.get("", response_model=list[ExerciseOut])
def list_exercises(
    _user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> list[Exercise]:
    return list(db.scalars(select(Exercise).order_by(Exercise.name)).all())


@router.get("/{exercise_id}", response_model=ExerciseOut)
def get_exercise(
    exercise_id: str,
    _user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> Exercise:
    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "exercise not found")
    return exercise


@router.get("/{exercise_id}/alternatives", response_model=list[AlternativeOut])
def get_alternatives(
    exercise_id: str,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> list[AlternativeOut]:
    return [
        AlternativeOut(
            id=ex.id,
            name=ex.name,
            pattern=ex.pattern,
            equipment=ex.equipment,
            media_url=ex.media_url,
            default_rest_s=ex.default_rest_s,
            substitution_count=count,
        )
        for ex, count in substitutions.alternatives(db, user.id, exercise_id)
    ]
