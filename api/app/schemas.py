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


class LoginOut(UserOut):
    """Login also returns the JWT in the body so a native client (Capacitor) can
    store it and authenticate via `Authorization: Bearer`. Web keeps using the
    httpOnly cookie and ignores this field."""

    token: str


# ---------- catalogue ----------
class ExerciseSummary(_Orm):
    id: str
    name: str
    pattern: MovementPattern
    equipment: Equipment
    media_url: str | None = None
    per_side: bool = False


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
    unit: str = "reps"  # "reps" or "seconds" (time-based holds)
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


# ---------- routine editing ----------
class ExerciseUpdate(BaseModel):
    target_sets: int
    rep_min: int
    rep_max: int
    rest_s: int | None  # null => use the exercise default


class ExerciseAdd(BaseModel):
    exercise_id: str
    target_sets: int = 3
    rep_min: int = 8
    rep_max: int = 12


class OrderBody(BaseModel):
    ids: list[str]  # a permutation of the current ids, in the new order


class DayRename(BaseModel):
    name: str


# ---------- state / today ----------
class StateOut(_Orm):
    routine_id: str
    next_position: int
    last_session_at: datetime | None


class TodayOut(BaseModel):
    next_position: int
    last_session_at: datetime | None
    day: RoutineDayOut
    recovery_warning: bool = False
    resume_after_break: bool = False


# ---------- body weight ----------
class BodyWeightPoint(_Orm):
    measured_on: date
    weight_kg: float


class BodyWeightSummary(BaseModel):
    """7-day moving average is the only accionable value (spec §5.6); the raw
    latest is exposed only for the treadmill estimate (spec §5.5)."""

    latest: float | None
    avg7: float | None
    delta_week: float | None
    points: list[BodyWeightPoint]


# ---------- progression (spec §5.2) ----------
class Suggestion(BaseModel):
    exercise_id: str
    last_weight_kg: float | None
    last_reps: list[int]
    all_at_rep_max: bool
    suggested_weight_kg: float | None
    last_session_on: date | None


# ---------- exercise detail ----------
class ExerciseHistoryEntry(BaseModel):
    """The top set of an exercise per past session (spec pantalla 3)."""

    session_on: date
    weight_kg: float
    reps: int


# ---------- history ----------
class SessionOut(_Orm):
    id: str
    routine_day_id: str
    position: int
    day_name: str
    started_at: datetime
    ended_at: datetime | None
    status: SessionStatus
    notes: str | None
    set_count: int = 0


# ---------- stats (volume, records) ----------
class VolumeGroup(BaseModel):
    """Effective (non-voided) working sets for a movement pattern in the last 7
    days (spec §7.1; useful range 10-20 per group)."""

    pattern: MovementPattern
    sets: int


class RecordOut(BaseModel):
    """Personal record per exercise: best estimated 1RM (Epley, spec §7.2)."""

    exercise_id: str
    exercise_name: str
    weight_kg: float
    reps: int
    one_rm: float
    achieved_on: date


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
