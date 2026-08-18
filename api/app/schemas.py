"""API wire schemas (Pydantic v2).

Weights travel as float (2.5 kg granularity is exact enough in this range) and
are stored as Numeric. Datetimes are ISO 8601; the server normalizes them to
naive UTC on write.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models.enums import Equipment, MovementPattern, SessionStatus
from .models.phase import PhaseKind


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
    # How to perform it, and what usually goes wrong (spec pantalla 3).
    technique: list[str] = Field(default_factory=list)
    mistakes: list[str] = Field(default_factory=list)


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


# ---------- notifications (spec §7.6) ----------
class NotificationOut(BaseModel):
    enabled: bool
    hour: int
    minute: int
    # Empty when the server has no VAPID key: the UI says reminders are
    # unavailable rather than offering a switch that cannot work.
    vapid_public_key: str
    devices: int


class NotificationIn(BaseModel):
    enabled: bool
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: PushKeys


# ---------- routine profiles ----------
class RoutineProfileOut(BaseModel):
    id: str
    name: str
    active: bool
    is_original: bool
    days: int
    sessions: int
    # False when deleting would destroy history or leave the user without a
    # routine; the UI hides the action instead of failing on tap.
    can_delete: bool


class ProfileName(BaseModel):
    name: str = Field(min_length=1, max_length=120)


# ---------- treadmill history (spec §5.5) ----------
class TreadmillEntry(BaseModel):
    id: str
    started_at: datetime
    duration_s: int
    # Null when no body weight is on record: the estimate needs it (spec §5.5).
    kcal: int | None


class TreadmillSummary(BaseModel):
    entries: list[TreadmillEntry]
    week_seconds: int
    week_kcal: int | None
    total_seconds: int
    sessions: int


# ---------- home dashboard ----------
class HomeOut(BaseModel):
    """Rolling 7-day picture plus what's next. Nulls mean "not measurable"."""

    # Which window the week_* figures cover: 7d | 30d | 365d | all.
    period: str
    next_position: int
    next_day_name: str
    next_exercises: int
    week_sessions: int
    week_sets: int
    week_volume_kg: float
    week_strength_seconds: int
    week_treadmill_seconds: int
    week_kcal: int | None
    bodyweight_avg7: float | None
    bodyweight_delta_week: float | None
    last_session_at: datetime | None
    volume: list[VolumeGroup]
    records: list[RecordOut]
    milestones: list["Milestone"]
    activity: list["ActivityPoint"]
    # Same-length window immediately before this one; null for "all time".
    prev_sessions: int | None
    prev_volume_kg: float | None
    prev_treadmill_seconds: int | None


class Milestone(BaseModel):
    """An all-time best the 1RM table cannot express (heaviest set, longest
    session, longest run). `kind` is a key; the UI supplies the wording."""

    kind: str
    value: float
    unit: str
    detail: str | None
    achieved_on: date | None


class ActivityPoint(BaseModel):
    """One bucket of the activity chart: a day for short windows, a month for
    long ones. `sessions` is 0 on rest days, which the chart draws as a gap."""

    bucket: date
    sessions: int
    volume_kg: float


# ---------- training phases ----------
class PhaseStatus(BaseModel):
    """How the phase is actually going. `verdict` and `duration` are keys the UI
    translates; nulls mean "not enough weigh-ins to say", never zero."""

    weeks_elapsed: float
    measurements: int
    actual_rate_pct: float | None
    verdict: str  # en_rumbo | demasiado_rapido | demasiado_lento | subiendo | bajando | sin_datos
    duration: str  # ok | larga | muy_larga
    suggest_end_weeks: int | None
    days_to_target: int | None


class PhaseOut(BaseModel):
    id: str
    kind: PhaseKind
    started_on: date
    ended_on: date | None
    target_rate_pct: float
    target_date: date | None
    target_weight_kg: float | None
    status: PhaseStatus | None


class PhaseIn(BaseModel):
    kind: PhaseKind
    # Omit to take the guideline default; out-of-range values are clamped, not
    # rejected, so the UI cannot ask for something unsafe by accident.
    target_rate_pct: float | None = None
    target_date: date | None = None
    target_weight_kg: float | None = None


class PhaseLimits(BaseModel):
    """What the UI may offer for each phase, straight from the guidelines."""

    kind: PhaseKind
    min_rate_pct: float
    default_rate_pct: float
    max_rate_pct: float
    suggest_end_weeks: int | None


class PhasesOut(BaseModel):
    enabled: bool
    current: PhaseOut | None
    history: list[PhaseOut]
    limits: list[PhaseLimits]


class PhaseAdviceIn(BaseModel):
    kind: PhaseKind
    # "menos_1" | "1_3" | "mas_3" — drives the surplus rate.
    training_age: str | None = None
    # "alta" | "media" | "baja" — drives the deficit rate.
    fat_level: str | None = None
    target_weight_kg: float | None = None
    target_date: date | None = None


class FeasibilityOut(BaseModel):
    """Whether the date and the weight can both be true. Arithmetic, not opinion."""

    weeks: float
    required_rate_pct: float
    verdict: str  # viable | muy_exigente | direccion_contraria
    safe_rate_pct: float
    reachable_weight_kg: float | None
    weeks_needed: float | None


class PhaseAdviceOut(BaseModel):
    recommended_rate_pct: float
    # Key the UI turns into the one-line reason for the number.
    rationale: str
    current_weight_kg: float | None
    feasibility: FeasibilityOut | None


class AssessmentIn(BaseModel):
    """Seven answers. All optional: a partial questionnaire still yields a plan,
    it is just built on the safer defaults."""

    objetivo: str | None = None
    grasa: str | None = None
    experiencia: str | None = None
    dieta_reciente: str | None = None
    fecha: str | None = None
    prioridad: str | None = None
    energia: str | None = None


class AssessmentOut(BaseModel):
    """A suggested plan, plus the reasoning as keys the UI writes out. Nothing is
    stored: it is a template the user may accept, edit or ignore."""

    kind: PhaseKind
    rate_pct: float
    weeks: int
    reasons: list[str]
    # Date the suggested block would end, so it can prefill the phase form.
    suggested_target_date: date


# --- routine assistant ---------------------------------------------------


class RoutineReviewIn(BaseModel):
    """The five things the routine cannot tell us. All optional: a partial
    questionnaire still yields a review, built on the safer defaults."""

    dias: int | None = None
    tiempo: str | None = None
    objetivo: str | None = None
    evitar: str | None = None
    prioridad: list[str] = []


class MuscleVolumeOut(BaseModel):
    muscle: str
    weekly_sets: float
    # bajo | justo | efectivo | alto — a key the UI translates.
    band: str


class SessionLengthOut(BaseModel):
    name: str
    minutes: int


class FindingOut(BaseModel):
    id: str
    kind: str
    severity: str
    detail: dict
    # None when the finding is worth knowing but has no safe automatic fix.
    action_kind: str | None


class RestructureSessionOut(BaseModel):
    name: str
    total_sets: int
    minutes: int
    exercises: list[str]


class RestructureOut(BaseModel):
    """A different split built from the same exercises. `fits` false means the
    work does not go into the time available, which is said rather than hidden."""

    days_per_week: int
    sessions: list[RestructureSessionOut]
    trimmed: list[dict]
    fits: bool
    under_target: list[str]
    sets_before: int
    sets_after: int


class RoutineReviewOut(BaseModel):
    days_per_week: int
    volumes: list[MuscleVolumeOut]
    session_minutes: list[SessionLengthOut]
    findings: list[FindingOut]
    restructure: RestructureOut | None


class RoutineApplyIn(BaseModel):
    answers: RoutineReviewIn
    # Ids of the findings the user ticked. Actions are recomputed server-side.
    accepted: list[str] = []


class ChangeOut(BaseModel):
    kind: str
    day: str
    exercise: str
    before: str
    after: str


class RoutineApplyOut(BaseModel):
    changed: int
    # Name of the profile the previous routine was saved as, so the UI can tell
    # the user exactly where to find the undo.
    snapshot: str | None
