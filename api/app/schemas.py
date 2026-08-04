"""API wire schemas (Pydantic v2).

Weights travel as float (2.5 kg granularity is exact enough in this range) and
are stored as Numeric. Datetimes are ISO 8601; the server normalizes them to
naive UTC on write.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models.enums import Equipment, MovementPattern, SessionStatus


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- auth ----------
class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(_Orm):
    id: str
    username: str
    display_name: str


# ---------- catalogue ----------
class ExerciseSummary(_Orm):
    id: str
    name: str
    pattern: MovementPattern
    equipment: Equipment
    media_url: str | None = None


class ExerciseOut(ExerciseSummary):
    description: str
    default_rest_s: int


class AlternativeOut(ExerciseSummary):
    """A same-pattern swap candidate (spec §5.3). `substitution_count` is how
    often this user has already swapped the planned exercise for this one."""

    substitution_count: int
    default_rest_s: int


# ---------- routine ----------
class RoutineDayExerciseOut(BaseModel):
    id: str
    order_index: int
    target_sets: int
    rep_min: int
    rep_max: int
    rest_s: int  # effective rest (override or exercise default)
    exercise: ExerciseSummary


class RoutineDayOut(BaseModel):
    id: str
    position: int
    name: str
    suggested_dow: int | None
    exercises: list[RoutineDayExerciseOut]


class RoutineOut(BaseModel):
    id: str
    name: str
    active: bool
    days: list[RoutineDayOut]


# ---------- state / today ----------
class StateOut(_Orm):
    routine_id: str
    next_position: int
    last_session_at: datetime | None


class TodayOut(BaseModel):
    next_position: int
    last_session_at: datetime | None
    day: RoutineDayOut


# ---------- history ----------
class SessionOut(_Orm):
    id: str
    routine_day_id: str
    started_at: datetime
    ended_at: datetime | None
    status: SessionStatus
    notes: str | None
    set_count: int = 0


# ---------- sync (push) ----------
class SessionIn(BaseModel):
    id: str
    routine_day_id: str
    started_at: datetime
    ended_at: datetime | None = None
    status: SessionStatus = SessionStatus.in_progress
    notes: str | None = None


class SetLogIn(BaseModel):
    id: str
    session_id: str
    exercise_id: str
    planned_exercise_id: str | None = None
    set_number: int
    weight_kg: float
    reps: int
    voided: bool = False
    created_at: datetime


class BodyWeightIn(BaseModel):
    id: str
    measured_on: date
    weight_kg: float


class TreadmillIn(BaseModel):
    id: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_s: int


class SyncPush(BaseModel):
    cursor: int = 0
    sessions: list[SessionIn] = Field(default_factory=list)
    set_logs: list[SetLogIn] = Field(default_factory=list)
    body_weights: list[BodyWeightIn] = Field(default_factory=list)
    treadmill_sessions: list[TreadmillIn] = Field(default_factory=list)


# ---------- sync (pull / result) ----------
class SyncEventOut(BaseModel):
    seq: int
    entity: str
    id: str
    data: dict


class SyncReject(BaseModel):
    entity: str
    id: str
    reason: str


class SyncResult(BaseModel):
    cursor: int
    accepted: int
    rejected: list[SyncReject]
    events: list[SyncEventOut]
