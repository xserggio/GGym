/**
 * Every user-visible string, in español de España. No loose literals in
 * components (CLAUDE.md). Voice: sentence-case, active verbs, no exclamation
 * marks, no emojis.
 */
export const es = {
  app: {
    title: "registro de fuerza",
  },
  actions: {
    start: "empezar",
    endSession: "terminar sesión",
    busy: "ocupada",
    skipSession: "saltar esta sesión",
    viewExercise: "ver ejercicio",
    settings: "ajustes",
    back: "volver",
    close: "cerrar",
  },
  session: {
    rest: "descanso",
    addFifteen: "+15",
    skipRest: "saltar",
    set: "serie",
    weight: "peso (kg)",
    reps: "reps",
  },
  today: {
    now: "toca ahora",
    treadmill: "cinta",
    bodyweight: "peso corporal",
    weekAverage: "media de la semana",
  },
  history: {
    empty:
      "aún no hay sesiones registradas. la primera aparecerá aquí en cuanto termines una.",
  },
  units: {
    kg: "kg",
  },
} as const;

export type Strings = typeof es;
