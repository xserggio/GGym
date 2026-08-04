import type { RoutineDayOut, SessionIn, SetLogIn } from "./api";

/** Client-side model of the session in progress. */
export interface LocalSet {
  id: string; // client UUID, the sync idempotency key
  setNumber: number;
  weightKg: number;
  reps: number;
  done: boolean;
}

export interface LocalExercise {
  rdeId: string;
  exerciseId: string;
  name: string;
  targetSets: number;
  repMin: number;
  repMax: number;
  sets: LocalSet[];
}

export interface ActiveSession {
  id: string;
  routineDayId: string;
  startedAt: string;
  exercises: LocalExercise[];
}

const DEFAULT_START_WEIGHT = 20; // empty olympic bar; the user adjusts with ±2,5

export function buildSession(day: RoutineDayOut): ActiveSession {
  return {
    id: crypto.randomUUID(),
    routineDayId: day.id,
    startedAt: new Date().toISOString(),
    exercises: day.exercises.map((rde) => ({
      rdeId: rde.id,
      exerciseId: rde.exercise.id,
      name: rde.exercise.name,
      targetSets: rde.target_sets,
      repMin: rde.rep_min,
      repMax: rde.rep_max,
      sets: Array.from({ length: rde.target_sets }, (_, i) => ({
        id: crypto.randomUUID(),
        setNumber: i + 1,
        weightKg: DEFAULT_START_WEIGHT,
        reps: rde.rep_max,
        done: false,
      })),
    })),
  };
}

export function sessionIn(
  session: ActiveSession,
  status: SessionIn["status"],
): SessionIn {
  return {
    id: session.id,
    routine_day_id: session.routineDayId,
    started_at: session.startedAt,
    ended_at: status === "completed" ? new Date().toISOString() : null,
    status,
  };
}

export function setLogIn(
  session: ActiveSession,
  exercise: LocalExercise,
  set: LocalSet,
): SetLogIn {
  return {
    id: set.id,
    session_id: session.id,
    exercise_id: exercise.exerciseId,
    planned_exercise_id: null,
    set_number: set.setNumber,
    weight_kg: set.weightKg,
    reps: set.reps,
    voided: false,
    created_at: new Date().toISOString(),
  };
}

export function doneCount(session: ActiveSession): number {
  return session.exercises.reduce(
    (acc, ex) => acc + ex.sets.filter((s) => s.done).length,
    0,
  );
}

export function totalSets(session: ActiveSession): number {
  return session.exercises.reduce((acc, ex) => acc + ex.sets.length, 0);
}
