import { es } from "../i18n/es";
import type {
  AlternativeOut,
  RoutineDayOut,
  SessionIn,
  SetLogIn,
  Suggestion,
} from "./api";
import { numEs } from "./format";

/** Client-side model of the session in progress. Each set carries its own
 * performed exercise, so a mid-slot substitution (machine busy after a couple of
 * sets) keeps the earlier sets attributed to the original exercise. */
export interface LocalSet {
  id: string; // client UUID, the sync idempotency key
  setNumber: number;
  weightKg: number;
  reps: number;
  done: boolean;
  exerciseId: string; // exercise actually performed for this set
  exerciseName: string;
  perSide: boolean;
}

export interface LocalExercise {
  rdeId: string;
  plannedExerciseId: string; // what the routine planned (stable, the slot identity)
  plannedName: string;
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
  notes: string;
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
    notes: "",
    exercises: day.exercises.map((rde) => {
      const sug = byExercise.get(rde.exercise.id);
      const startWeight = sug?.suggested_weight_kg ?? DEFAULT_START_WEIGHT;
      return {
        rdeId: rde.id,
        plannedExerciseId: rde.exercise.id,
        plannedName: rde.exercise.name,
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
          exerciseId: rde.exercise.id,
          exerciseName: rde.exercise.name,
          perSide: rde.exercise.per_side,
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
    notes: session.notes.trim() || null,
  };
}

export function setLogIn(
  session: ActiveSession,
  slot: LocalExercise,
  set: LocalSet,
): SetLogIn {
  const substituted = set.exerciseId !== slot.plannedExerciseId;
  return {
    id: set.id,
    session_id: session.id,
    exercise_id: set.exerciseId,
    planned_exercise_id: substituted ? slot.plannedExerciseId : null,
    set_number: set.setNumber,
    weight_kg: set.weightKg,
    reps: set.reps,
    voided: false,
    created_at: new Date().toISOString(),
  };
}

/** Substitute the remaining (not-yet-done) sets of a slot for an alternative
 * (machine busy). Sets already done keep the exercise they were logged as, so
 * the record shows which sets were which exercise. */
export function substitute(
  session: ActiveSession,
  slotIdx: number,
  alt: AlternativeOut,
): ActiveSession {
  return {
    ...session,
    exercises: session.exercises.map((slot, i) =>
      i !== slotIdx
        ? slot
        : {
            ...slot,
            sets: slot.sets.map((s) =>
              s.done
                ? s
                : {
                    ...s,
                    exerciseId: alt.id,
                    exerciseName: alt.name,
                    perSide: alt.per_side,
                  },
            ),
          },
    ),
  };
}

export interface SessionSummary {
  positionLabel: string;
  durationMin: number;
  volumeKg: number;
  setsDone: number;
  kcal: number | null;
  exercises: { name: string; weightKg: number; reps: number }[];
}

/**
 * Resistance-training MET (Compendium of Physical Activities, code 02050 family:
 * ~3.5 light … 6.0 vigorous; 5.0 is a defensible whole-session value that already
 * accounts for rest periods). kcal ≈ MET × body-weight-kg × hours — the standard
 * method, honest as an estimate. Needs the user's real weight; null without it.
 */
const RESISTANCE_MET = 5.0;

export function summarize(
  session: ActiveSession,
  bodyweightKg: number | null,
): Omit<SessionSummary, "positionLabel"> {
  const doneSets = session.exercises.flatMap((slot) =>
    slot.sets.filter((s) => s.done),
  );
  const setsDone = doneSets.length;
  const volumeKg = doneSets.reduce((acc, s) => acc + s.weightKg * s.reps, 0);
  const durationMin = Math.max(
    1,
    Math.round((Date.now() - Date.parse(session.startedAt)) / 60000),
  );
  const kcal =
    bodyweightKg != null
      ? Math.round(RESISTANCE_MET * bodyweightKg * (durationMin / 60))
      : null;

  // Best set per performed exercise (heaviest, then most reps).
  const best = new Map<string, { name: string; weightKg: number; reps: number }>();
  for (const s of doneSets) {
    const cur = best.get(s.exerciseId);
    if (!cur || s.weightKg > cur.weightKg || (s.weightKg === cur.weightKg && s.reps > cur.reps)) {
      best.set(s.exerciseId, { name: s.exerciseName, weightKg: s.weightKg, reps: s.reps });
    }
  }
  return { durationMin, volumeKg, setsDone, kcal, exercises: [...best.values()] };
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
