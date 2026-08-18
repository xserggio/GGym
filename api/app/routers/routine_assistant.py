"""The routine assistant (spec pantalla 5, extension).

Three steps, three endpoints: review the routine, preview what the accepted
findings would do, then apply them. The review is stateless and idempotent, so
it can be re-run freely; only `apply` writes, and it snapshots first.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as OrmSession

from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import (
    ChangeOut,
    FindingOut,
    MuscleVolumeOut,
    RestructureOut,
    RestructureSessionOut,
    RoutineApplyIn,
    RoutineApplyOut,
    RoutineReviewIn,
    RoutineReviewOut,
    SessionLengthOut,
)
from ..services import routine_apply, routine_restructure, routine_review

router = APIRouter(prefix="/me/routine/assistant", tags=["routine"])


def _restructure_out(plan) -> RestructureOut | None:
    if plan is None:
        return None
    return RestructureOut(
        days_per_week=plan.days_per_week,
        sessions=[
            RestructureSessionOut(
                name=s.name,
                total_sets=s.total_sets,
                minutes=s.minutes(),
                exercises=[r.name for r in s.rows],
            )
            for s in plan.sessions
        ],
        trimmed=plan.trimmed,
        fits=plan.fits,
        under_target=plan.under_target,
        sets_before=plan.sets_before,
        sets_after=plan.sets_after,
    )


@router.post("/review", response_model=RoutineReviewOut)
def review(
    body: RoutineReviewIn,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> RoutineReviewOut:
    """Read the routine and say what is worth changing.

    Writes nothing. Every finding names a specific exercise in a specific
    session, and the ones that depend on history stay quiet until there is
    enough of it.
    """
    answers = body.model_dump()
    result = routine_review.review(db, user.id, answers)
    days = routine_review.load_routine(db, user.id)
    plan = routine_restructure.restructure(
        days, result.days_per_week, int(answers.get("tiempo") or 60)
    )
    return RoutineReviewOut(
        days_per_week=result.days_per_week,
        volumes=[
            MuscleVolumeOut(muscle=v.muscle, weekly_sets=v.weekly_sets, band=v.band)
            for v in result.volumes
        ],
        session_minutes=[
            SessionLengthOut(name=name, minutes=minutes)
            for name, minutes in result.session_minutes
        ],
        findings=[
            FindingOut(
                id=f.id,
                kind=f.kind,
                severity=f.severity,
                detail=f.detail,
                action_kind=f.action.kind if f.action else None,
            )
            for f in result.findings
        ],
        restructure=_restructure_out(plan),
    )


@router.post("/preview", response_model=list[ChangeOut])
def preview(
    body: RoutineApplyIn,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> list[ChangeOut]:
    """Exactly what would change, before anything does. Same review the apply
    runs, so what she confirms is what she gets."""
    changes = routine_apply.preview(
        db, user.id, body.answers.model_dump(), body.accepted
    )
    return [
        ChangeOut(
            kind=c.kind,
            day=c.day,
            exercise=c.exercise,
            before=c.before,
            after=c.after,
        )
        for c in changes
    ]


@router.post("/apply", response_model=RoutineApplyOut)
def apply(
    body: RoutineApplyIn,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> RoutineApplyOut:
    """Apply the ticked findings, after copying the routine to a dated profile.

    The request carries only ids; the edits themselves are recomputed here, so a
    client can never ask for a change the assistant did not propose.
    """
    changed, snapshot = routine_apply.apply(
        db, user.id, body.answers.model_dump(), body.accepted, date.today()
    )
    db.commit()
    return RoutineApplyOut(changed=changed, snapshot=snapshot)


@router.post("/restructure", response_model=RoutineApplyOut)
def restructure(
    body: RoutineReviewIn,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> RoutineApplyOut:
    """Build the redistributed split as a new profile and switch to it. The
    routine she had stays untouched, just no longer active."""
    name = routine_apply.apply_restructure(
        db, user.id, body.model_dump(), date.today()
    )
    db.commit()
    return RoutineApplyOut(changed=1, snapshot=name)
