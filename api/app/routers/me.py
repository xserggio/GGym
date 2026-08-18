from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..deps import get_current_user, get_db
from ..models import RoutineDay, Session, SetLog, User
from ..models.enums import SessionStatus
from ..schemas import (
    BodyWeightSummary,
    ConfidenceOut,
    LabOut,
    LoadOut,
    MuscleRecoveryOut,
    ExerciseHistoryEntry,
    RecordOut,
    RoutineOut,
    SessionOut,
    StateOut,
    Suggestion,
    HomeOut,
    TodayOut,
    TreadmillSummary,
    VolumeGroup,
)
from ..services import (
    bodyweight,
    export,
    home,
    progression,
    recovery,
    stats,
    treadmill,
    wheel,
)

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
        recovery_warning=wheel.recovery_warning(db, user.id),
        resume_after_break=wheel.resume_after_break(db, user.id),
    )


@router.post("/skip", response_model=StateOut)
def skip_session(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> StateOut:
    state = wheel.skip(db, user.id)
    db.commit()
    return StateOut.model_validate(state)


@router.get("/day/{day_id}/suggestions", response_model=list[Suggestion])
def get_suggestions(
    day_id: str,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> list[Suggestion]:
    return progression.suggestions_for_day(
        db, user.id, day_id, deload=wheel.resume_after_break(db, user.id)
    )


@router.get("/bodyweight", response_model=BodyWeightSummary)
def get_bodyweight(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> BodyWeightSummary:
    return bodyweight.summary(db, user.id)


@router.get("/history", response_model=list[SessionOut])
def get_history(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> list[SessionOut]:
    rows = db.execute(
        select(Session, RoutineDay, func.count(SetLog.id))
        .join(RoutineDay, RoutineDay.id == Session.routine_day_id)
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
            position=day.position,
            day_name=day.name,
            started_at=s.started_at,
            ended_at=s.ended_at,
            status=s.status,
            notes=s.notes,
            set_count=count,
        )
        for s, day, count in rows
    ]


@router.get("/export")
def get_export(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> dict:
    return export.export_all(db, user)


@router.get("/exercises/{exercise_id}/history", response_model=list[ExerciseHistoryEntry])
def get_exercise_history(
    exercise_id: str,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> list[ExerciseHistoryEntry]:
    return stats.exercise_history(db, user.id, exercise_id)


@router.get("/volume", response_model=list[VolumeGroup])
def get_volume(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> list[VolumeGroup]:
    return stats.weekly_volume(db, user.id)


@router.get("/records", response_model=list[RecordOut])
def get_records(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> list[RecordOut]:
    return stats.records(db, user.id)


@router.get("/home", response_model=HomeOut)
def get_home(
    period: str = "7d",
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> HomeOut:
    """Everything the Inicio tab shows, in one request (one round trip offline).

    `period` selects the window for the totals: 7d, 30d, 365d or all.
    """
    if period not in home.PERIOD_DAYS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown period")
    return home.summary(db, user.id, period)


@router.get("/treadmill", response_model=TreadmillSummary)
def get_treadmill(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> TreadmillSummary:
    return treadmill.summary(db, user.id)


@router.get("/lab", response_model=LabOut)
def lab(
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> LabOut:
    """Recovery per muscle, recent load, and how much history both rest on.

    Everything here is derived from logged sets; nothing is measured. The parts
    that need more history than exists come back as null so the screen can say
    "not yet" rather than print a number that means nothing.
    """
    items = recovery.recovery(db, user.id)
    balance = recovery.load(db, user.id)
    return LabOut(
        recovery=(
            [
                MuscleRecoveryOut(
                    muscle=m.muscle,
                    percent=m.percent,
                    band=m.band,
                    hours_to_fresh=m.hours_to_fresh,
                )
                for m in items
            ]
            if items is not None
            else None
        ),
        overall_percent=recovery.overall(items) if items else None,
        load=(
            LoadOut(
                ratio=balance.ratio,
                band=balance.band,
                acute_sets=balance.acute_sets,
                chronic_weekly_sets=balance.chronic_weekly_sets,
            )
            if balance
            else None
        ),
        confidence=ConfidenceOut(**vars(recovery.confidence(db, user.id))),
    )
