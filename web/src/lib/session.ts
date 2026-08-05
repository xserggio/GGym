import { es } from "../i18n/es";
import type {
  AlternativeOut,
  RoutineDayOut,
  SessionIn,
  SetLogIn,
  Suggestion,
} from "./api";
import { numEs } from "./format";

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
  exerciseId: string; // performed exercise (changes on substitution)
  plannedExerciseId: string; // what the routine planned (stable)
  name: string;
  restS: number;
  targetSets: number;
  repMin: number;
  repMax: number;
  /** Progression hint (spec §5.2), or null when there's nothing to suggest. */
  suggestion: string | null;
  sets: LocalSet[];
}

export interface ActiveSession {
  id: string;
  routineDayId: string;
  startedAt: string;
  exercises: LocalExercise[];
}

const DEFAULT_START_WEIGHT = 20; // empty olympic bar; the user adjusts with ±2,5

function progressionHint(repMax: number, sug: Suggestion | undefined): string | null {
  if (
    !sug ||
    !sug.all_at_rep_max ||
    sug.last_weight_kg == null ||
    sug.suggested_weight_kg == null ||
    sug.suggested_weight_kg <= sug.last_weight_kg
  ) {
    return null;
  }
  const bump = sug.suggested_weight_kg - sug.last_weight_kg;
  return es.session.progressionHint(sug.last_reps.length, repMax, numEs(bump));
}

export function buildSession(
  day: RoutineDayOut,
  suggestions: Suggestion[] = [],
): ActiveSession {
  const byExercise = new Map(suggestions.map((s) => [s.exercise_id, s]));
  return {
    id: crypto.randomUUID(),
    routineDayId: day.id,
    startedAt: new Date().toISOString(),
    exercises: day.exercises.map((rde) => {
      const sug = byExercise.get(rde.exercise.id);
      const startWeight = sug?.suggested_weight_kg ?? DEFAULT_START_WEIGHT;
      return {
        rdeId: rde.id,
        exerciseId: rde.exercise.id,
        plannedExerciseId: rde.exercise.id,
        name: rde.exercise.name,
        restS: rde.rest_s,
        targetSets: rde.target_sets,
        repMin: rde.rep_min,
        repMax: rde.rep_max,
        suggestion: progressionHint(rde.rep_max, sug),
        sets: Array.from({ length: rde.target_sets }, (_, i) => ({
          id: crypto.randomUUID(),
          setNumber: i + 1,
          weightKg: startWeight,
          reps: rde.rep_max,
          done: false,
        })),
      };
    }),
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
  const substituted = exercise.exerciseId !== exercise.plannedExerciseId;
  return {
    id: set.id,
    session_id: session.id,
    exercise_id: exercise.exerciseId,
    planned_exercise_id: substituted ? exercise.plannedExerciseId : null,
    set_number: set.setNumber,
    weight_kg: set.weightKg,
    reps: set.reps,
    voided: false,
    created_at: new Date().toISOString(),
  };
}

/** Swap the performed exercise for an alternative, keeping the planned one. */
export function swapExercise(
  session: ActiveSession,
  exerciseIdx: number,
  alt: AlternativeOut,
): ActiveSession {
  return {
    ...session,
    exercises: session.exercises.map((ex, i) =>
      i !== exerciseIdx
        ? ex
        : {
            ...ex,
            exerciseId: alt.id,
            name: alt.name,
            restS: alt.default_rest_s,
            suggestion: null,
          },
    ),
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
