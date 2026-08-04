from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..deps import get_current_user, get_db
from ..models import Session, SetLog, User
from ..models.enums import SessionStatus
from ..schemas import RoutineOut, SessionOut, StateOut, TodayOut
from ..services import wheel

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/state", response_model=StateOut)
def get_state(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> StateOut:
    return StateOut.model_validate(wheel.get_state(db, user.id))


@router.get("/routine", response_model=RoutineOut)
def get_routine(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> RoutineOut:
    return wheel.routine_out(db, wheel.get_active_routine(db, user.id))


@router.get("/today", response_model=TodayOut)
def get_today(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> TodayOut:
    state = wheel.get_state(db, user.id)
    return TodayOut(
        next_position=state.next_position,
        last_session_at=state.last_session_at,
        day=wheel.current_day_out(db, user.id),
    )


@router.get("/history", response_model=list[SessionOut])
def get_history(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> list[SessionOut]:
    rows = db.execute(
        select(Session, func.count(SetLog.id))
        .outerjoin(
            SetLog,
            (SetLog.session_id == Session.id) & (SetLog.voided.is_(False)),
        )
        .where(
            Session.user_id == user.id,
            Session.status != SessionStatus.in_progress,
        )
        .group_by(Session.id)
        .order_by(Session.started_at.desc())
        .limit(50)
    ).all()
    return [
        SessionOut(
            id=s.id,
            routine_day_id=s.routine_day_id,
            started_at=s.started_at,
            ended_at=s.ended_at,
            status=s.status,
            notes=s.notes,
            set_count=count,
        )
        for s, count in rows
    ]
