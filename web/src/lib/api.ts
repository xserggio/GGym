import type { components } from "./api-types";

type Schemas = components["schemas"];

export type UserOut = Schemas["UserOut"];
export type LoginOut = Schemas["LoginOut"];
export type StateOut = Schemas["StateOut"];
export type TodayOut = Schemas["TodayOut"];
export type RoutineOut = Schemas["RoutineOut"];
export type RoutineDayOut = Schemas["RoutineDayOut"];
export type RoutineDayExerciseOut = Schemas["RoutineDayExerciseOut"];
export type ExerciseSummary = Schemas["ExerciseSummary"];
export type ExerciseOut = Schemas["ExerciseOut"];
export type ExerciseHistoryEntry = Schemas["ExerciseHistoryEntry"];
export type AlternativeOut = Schemas["AlternativeOut"];
export type SessionOut = Schemas["SessionOut"];
export type BodyWeightSummary = Schemas["BodyWeightSummary"];
export type VolumeGroup = Schemas["VolumeGroup"];
export type RecordOut = Schemas["RecordOut"];
export type Suggestion = Schemas["Suggestion"];
export type SessionIn = Schemas["SessionIn"];
export type SetLogIn = Schemas["SetLogIn"];
export type BodyWeightIn = Schemas["BodyWeightIn"];
export type TreadmillIn = Schemas["TreadmillIn"];
export type NotificationOut = Schemas["NotificationOut"];
export type RoutineProfileOut = Schemas["RoutineProfileOut"];
export type HomeOut = Schemas["HomeOut"];
export type TreadmillSummary = Schemas["TreadmillSummary"];
export type TreadmillEntry = Schemas["TreadmillEntry"];
export type Milestone = Schemas["Milestone"];
export type ActivityPoint = Schemas["ActivityPoint"];
export type PhasesOut = Schemas["PhasesOut"];
export type PhaseOut = Schemas["PhaseOut"];
export type PhaseKind = Schemas["PhaseKind"];
export type PhaseAdviceOut = Schemas["PhaseAdviceOut"];
export type AssessmentOut = Schemas["AssessmentOut"];
export type RoutineReviewIn = Schemas["RoutineReviewIn"];
export type RoutineReviewOut = Schemas["RoutineReviewOut"];
export type FindingOut = Schemas["FindingOut"];
export type MuscleVolumeOut = Schemas["MuscleVolumeOut"];
export type RestructureOut = Schemas["RestructureOut"];
export type ChangeOut = Schemas["ChangeOut"];
export type LabOut = Schemas["LabOut"];
export type MuscleRecoveryOut = Schemas["MuscleRecoveryOut"];
export type RoutineApplyOut = Schemas["RoutineApplyOut"];
/** What the backend expects from `PushSubscription.toJSON()` (keys required). */
export interface PushSubscriptionBody {
  endpoint: string;
  keys: { p256dh: string; auth: string };
}
export type SyncPush = Schemas["SyncPush"];
export type SyncResult = Schemas["SyncResult"];

// API root. Web (same-origin): "/api" in dev (Vite proxy), "<base>api" e.g.
// "/gym/api" in prod (nginx). Native (Capacitor): absolute VITE_API_BASE.
const BASE = import.meta.env.VITE_API_BASE ?? `${import.meta.env.BASE_URL}api`;

/**
 * True when the API lives on another origin — the native (Capacitor) build,
 * where the page is served from the device and no cookie is shared. Those
 * clients authenticate with the bearer token instead.
 */
export const crossOrigin = /^https?:\/\//.test(BASE);

const TOKEN_KEY = "gym.token";

/** Native clients store the JWT and authenticate via Bearer. Web keeps the
 * httpOnly cookie and never sets this. */
export function setAuthToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // storage unavailable — ignore
  }
}

function authHeader(): Record<string, string> {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...authHeader(), ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // non-JSON error body; keep statusText
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginOut>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: async () => {
    await request<void>("/auth/logout", { method: "POST" }).catch(() => undefined);
    setAuthToken(null); // native: drop the bearer token too
  },
  me: () => request<UserOut>("/auth/me"),
  today: () => request<TodayOut>("/me/today"),
  suggestions: (dayId: string) =>
    request<Suggestion[]>(`/me/day/${dayId}/suggestions`),
  state: () => request<StateOut>("/me/state"),
  skip: () => request<StateOut>("/me/skip", { method: "POST" }),
  routine: () => request<RoutineOut>("/me/routine"),
  history: () => request<SessionOut[]>("/me/history"),
  bodyweight: () => request<BodyWeightSummary>("/me/bodyweight"),
  volume: () => request<VolumeGroup[]>("/me/volume"),
  records: () => request<RecordOut[]>("/me/records"),
  exportData: () => request<Record<string, unknown>>("/me/export"),
  updateExercise: (
    rdeId: string,
    body: { target_sets: number; rep_min: number; rep_max: number; rest_s: number | null },
  ) =>
    request<RoutineOut>(`/me/routine/exercises/${rdeId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  removeExercise: (rdeId: string) =>
    request<RoutineOut>(`/me/routine/exercises/${rdeId}`, { method: "DELETE" }),
  addExercise: (dayId: string, exerciseId: string) =>
    request<RoutineOut>(`/me/routine/days/${dayId}/exercises`, {
      method: "POST",
      body: JSON.stringify({ exercise_id: exerciseId }),
    }),
  reorderExercises: (dayId: string, ids: string[]) =>
    request<RoutineOut>(`/me/routine/days/${dayId}/exercise-order`, {
      method: "PUT",
      body: JSON.stringify({ ids }),
    }),
  reorderDays: (ids: string[]) =>
    request<RoutineOut>("/me/routine/day-order", {
      method: "PUT",
      body: JSON.stringify({ ids }),
    }),
  renameDay: (dayId: string, name: string) =>
    request<RoutineOut>(`/me/routine/days/${dayId}`, {
      method: "PATCH",
      body: JSON.stringify({ name }),
    }),
  exercises: () => request<ExerciseSummary[]>("/exercises"),
  exercise: (exerciseId: string) =>
    request<ExerciseOut>(`/exercises/${exerciseId}`),
  exerciseHistory: (exerciseId: string) =>
    request<ExerciseHistoryEntry[]>(`/me/exercises/${exerciseId}/history`),
  alternatives: (exerciseId: string) =>
    request<AlternativeOut[]>(`/exercises/${exerciseId}/alternatives`),
  sync: (push: SyncPush) =>
    request<SyncResult>("/sync", { method: "POST", body: JSON.stringify(push) }),
  home: (period = "7d") => request<HomeOut>(`/me/home?period=${period}`),
  treadmill: () => request<TreadmillSummary>("/me/treadmill"),
  profiles: () => request<RoutineProfileOut[]>("/me/routine/profiles"),
  activateProfile: (id: string) =>
    request<RoutineProfileOut[]>(`/me/routine/profiles/${id}/activate`, {
      method: "POST",
    }),
  duplicateProfile: (id: string, name: string) =>
    request<RoutineProfileOut[]>(`/me/routine/profiles/${id}/duplicate`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  renameProfile: (id: string, name: string) =>
    request<RoutineProfileOut[]>(`/me/routine/profiles/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ name }),
    }),
  deleteProfile: (id: string) =>
    request<RoutineProfileOut[]>(`/me/routine/profiles/${id}`, { method: "DELETE" }),
  restoreProfile: () =>
    request<RoutineProfileOut[]>("/me/routine/profiles/restore", { method: "POST" }),
  routineReview: (answers: RoutineReviewIn) =>
    request<RoutineReviewOut>("/me/routine/assistant/review", {
      method: "POST",
      body: JSON.stringify(answers),
    }),
  routinePreview: (answers: RoutineReviewIn, accepted: string[]) =>
    request<ChangeOut[]>("/me/routine/assistant/preview", {
      method: "POST",
      body: JSON.stringify({ answers, accepted }),
    }),
  routineApply: (answers: RoutineReviewIn, accepted: string[]) =>
    request<RoutineApplyOut>("/me/routine/assistant/apply", {
      method: "POST",
      body: JSON.stringify({ answers, accepted }),
    }),
  routineRestructure: (answers: RoutineReviewIn) =>
    request<RoutineApplyOut>("/me/routine/assistant/restructure", {
      method: "POST",
      body: JSON.stringify(answers),
    }),
  lab: () => request<LabOut>("/me/lab"),
  phases: () => request<PhasesOut>("/me/phases"),
  setPhasesEnabled: (enabled: boolean) =>
    request<PhasesOut>("/me/phases", {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    }),
  phaseAssessment: (answers: Record<string, string | null>) =>
    request<AssessmentOut>("/me/phases/assessment", {
      method: "POST",
      body: JSON.stringify(answers),
    }),
  phaseAdvice: (body: {
    kind: PhaseKind;
    training_age?: string | null;
    fat_level?: string | null;
    target_weight_kg?: number | null;
    target_date?: string | null;
  }) =>
    request<PhaseAdviceOut>("/me/phases/advice", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  startPhase: (body: {
    kind: PhaseKind;
    target_rate_pct?: number | null;
    target_date?: string | null;
    target_weight_kg?: number | null;
  }) => request<PhasesOut>("/me/phases", { method: "POST", body: JSON.stringify(body) }),
  endPhase: () => request<PhasesOut>("/me/phases", { method: "DELETE" }),
  notifications: () => request<NotificationOut>("/me/notifications"),
  setNotifications: (body: { enabled: boolean; hour: number; minute: number }) =>
    request<NotificationOut>("/me/notifications", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  subscribePush: (sub: PushSubscriptionBody) =>
    request<NotificationOut>("/me/notifications/subscribe", {
      method: "POST",
      body: JSON.stringify(sub),
    }),
  unsubscribePush: (endpoint: string) =>
    request<void>(
      `/me/notifications/subscribe?endpoint=${encodeURIComponent(endpoint)}`,
      { method: "DELETE" },
    ),
};
