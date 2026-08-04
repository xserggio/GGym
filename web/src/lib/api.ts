import type { components } from "./api-types";

type Schemas = components["schemas"];

export type UserOut = Schemas["UserOut"];
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
export type SyncPush = Schemas["SyncPush"];
export type SyncResult = Schemas["SyncResult"];

const BASE = "/api"; // Vite proxies /api -> the FastAPI backend (same-origin cookies).

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
    headers: { "Content-Type": "application/json", ...init?.headers },
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
    request<UserOut>("/auth/login", {
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
  exercises: () => request<ExerciseSummary[]>("/exercises"),
  alternatives: (exerciseId: string) =>
    request<AlternativeOut[]>(`/exercises/${exerciseId}/alternatives`),
  sync: (push: SyncPush) =>
    request<SyncResult>("/sync", { method: "POST", body: JSON.stringify(push) }),
};
