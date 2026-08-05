from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session as OrmSession

from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import DayRename, ExerciseAdd, ExerciseUpdate, OrderBody, RoutineOut
from ..services import routine_edit, wheel

router = APIRouter(prefix="/me/routine", tags=["routine"])


def _routine_out(db: OrmSession, user: User) -> RoutineOut:
    return wheel.routine_out(db, wheel.get_active_routine(db, user.id))


@router.patch("/exercises/{rde_id}", response_model=RoutineOut)
def update_exercise(
    rde_id: str,
    body: ExerciseUpdate,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> RoutineOut:
    routine_edit.update_exercise(db, user.id, rde_id, body)
    db.commit()
    return _routine_out(db, user)


@router.delete("/exercises/{rde_id}", response_model=RoutineOut)
def remove_exercise(
    rde_id: str,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> RoutineOut:
    routine_edit.remove_exercise(db, user.id, rde_id)
    db.commit()
    return _routine_out(db, user)


@router.post(
    "/days/{day_id}/exercises",
    response_model=RoutineOut,
    status_code=status.HTTP_201_CREATED,
)
def add_exercise(
    day_id: str,
    body: ExerciseAdd,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> RoutineOut:
    routine_edit.add_exercise(db, user.id, day_id, body)
    db.commit()
    return _routine_out(db, user)


@router.put("/days/{day_id}/exercise-order", response_model=RoutineOut)
def reorder_exercises(
    day_id: str,
    body: OrderBody,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> RoutineOut:
    routine_edit.reorder_exercises(db, user.id, day_id, body.ids)
    db.commit()
    return _routine_out(db, user)


@router.patch("/days/{day_id}", response_model=RoutineOut)
def rename_day(
    day_id: str,
    body: DayRename,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> RoutineOut:
    routine_edit.rename_day(db, user.id, day_id, body.name)
    db.commit()
    return _routine_out(db, user)


@router.put("/day-order", response_model=RoutineOut)
def reorder_days(
    body: OrderBody,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> RoutineOut:
    routine_edit.reorder_days(db, user.id, body.ids)
    db.commit()
    return _routine_out(db, user)
