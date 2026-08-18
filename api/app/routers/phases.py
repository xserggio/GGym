from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session as OrmSession

from ..deps import get_current_user, get_db
from ..models import PhaseKind, User
from ..schemas import (
    AssessmentIn,
    AssessmentOut,
    FeasibilityOut,
    PhaseAdviceIn,
    PhaseAdviceOut,
    PhaseIn,
    PhaseLimits,
    PhasesOut,
)
from ..services import assessment, phases

router = APIRouter(prefix="/me/phases", tags=["phases"])


class PhasesToggle(BaseModel):
    enabled: bool


def _limits() -> list[PhaseLimits]:
    return [
        PhaseLimits(
            kind=kind,
            min_rate_pct=low,
            default_rate_pct=default,
            max_rate_pct=high,
            suggest_end_weeks=phases.SUGGEST_END_WEEKS[kind] or None,
        )
        for kind, (low, default, high) in phases.LIMITS.items()
    ]


def _out(db: OrmSession, user: User) -> PhasesOut:
    current = phases.active(db, user.id)
    return PhasesOut(
        enabled=user.phases_enabled,
        current=phases.out(db, user.id, current) if current else None,
        history=[
            phases.out(db, user.id, p)
            for p in phases.history(db, user.id)
            if p.ended_on is not None
        ],
        limits=_limits(),
    )


def _require_enabled(user: User) -> None:
    if not user.phases_enabled:
        raise HTTPException(status.HTTP_409_CONFLICT, "phases are disabled")


@router.get("", response_model=PhasesOut)
def read(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> PhasesOut:
    return _out(db, user)


@router.patch("", response_model=PhasesOut)
def toggle(
    body: PhasesToggle,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> PhasesOut:
    """Turning the feature off closes any running phase rather than leaving it
    ticking invisibly, so re-enabling never resurrects a stale one."""
    user.phases_enabled = body.enabled
    if not body.enabled and phases.active(db, user.id) is not None:
        phases.end(db, user.id)
    db.flush()
    out = _out(db, user)
    db.commit()
    return out


@router.post("", response_model=PhasesOut)
def start(
    body: PhaseIn,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> PhasesOut:
    _require_enabled(user)
    phases.start(
        db,
        user.id,
        body.kind,
        body.target_rate_pct,
        body.target_date,
        body.target_weight_kg,
    )
    out = _out(db, user)
    db.commit()
    return out


@router.delete("", response_model=PhasesOut)
def finish(
    user: User = Depends(get_current_user), db: OrmSession = Depends(get_db)
) -> PhasesOut:
    _require_enabled(user)
    phases.end(db, user.id)
    out = _out(db, user)
    db.commit()
    return out


@router.post("/advice", response_model=PhaseAdviceOut)
def advice(
    body: PhaseAdviceIn,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> PhaseAdviceOut:
    """Propose a rate from two questions, and check a target date against it.

    Deliberately deterministic: the same answers always give the same number, so
    the reason can be shown and argued with. Nothing is stored.
    """
    rate, rationale = phases.recommend(body.kind, body.training_age, body.fat_level)
    weight = phases.current_weight(db, user.id)

    check = None
    if weight is not None and body.target_weight_kg and body.target_date:
        result = phases.feasibility(
            body.kind, weight, body.target_weight_kg, body.target_date
        )
        if result is not None:
            check = FeasibilityOut(**vars(result))

    return PhaseAdviceOut(
        recommended_rate_pct=rate,
        rationale=rationale,
        current_weight_kg=weight,
        feasibility=check,
    )


@router.post("/assessment", response_model=AssessmentOut)
def assess(
    body: AssessmentIn,
    user: User = Depends(get_current_user),
    db: OrmSession = Depends(get_db),
) -> AssessmentOut:
    """Suggest which phase to run, how fast and for how long.

    Deterministic and stateless: the same answers always give the same plan, so
    the reasons can be shown and argued with. The user still decides.
    """
    plan = assessment.evaluate(body.model_dump())
    return AssessmentOut(
        kind=plan.kind,
        rate_pct=plan.rate_pct,
        weeks=plan.weeks,
        reasons=plan.reasons,
        suggested_target_date=date.today() + timedelta(weeks=plan.weeks),
    )
