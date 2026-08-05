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
export type AlternativeOut = Schemas["AlternativeOut"];
export type SessionOut = Schemas["SessionOut"];
export type BodyWeightSummary = Schemas["BodyWeightSummary"];
export type VolumeGroup = Schemas["VolumeGroup"];
export type RecordOut = Schemas["RecordOut"];
export type SessionIn = Schemas["SessionIn"];
export type SetLogIn = Schemas["SetLogIn"];
export type BodyWeightIn = Schemas["BodyWeightIn"];
export type TreadmillIn = Schemas["TreadmillIn"];
export type SyncPush = Schemas["SyncPush"];
export type SyncResult = Schemas["SyncResult"];

// API root. Web (same-origin): "/api" in dev (Vite proxy), "<base>api" e.g.
// "/gym/api" in prod (nginx). Native (Capacitor): absolute VITE_API_BASE.
const BASE = import.meta.env.VITE_API_BASE ?? `${import.meta.env.BASE_URL}api`;

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
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  me: () => request<UserOut>("/auth/me"),
  today: () => request<TodayOut>("/me/today"),
  state: () => request<StateOut>("/me/state"),
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
  exercises: () => request<ExerciseSummary[]>("/exercises"),
  alternatives: (exerciseId: string) =>
    request<AlternativeOut[]>(`/exercises/${exerciseId}/alternatives`),
  sync: (push: SyncPush) =>
    request<SyncResult>("/sync", { method: "POST", body: JSON.stringify(push) }),
};
