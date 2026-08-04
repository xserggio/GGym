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
    logout: "salir",
  },
  login: {
    user: "usuario",
    password: "contraseña",
    enter: "entrar",
    error: "usuario o contraseña incorrectos",
    loading: "entrando…",
  },
  today: {
    now: "toca ahora",
    treadmill: "cinta",
    bodyweight: "peso corporal",
    weekAverage: "media de la semana",
    session: "sesión",
    exercises: "ejercicios",
    sets: "series",
  },
  session: {
    rest: "descanso",
    addFifteen: "+15",
    skipRest: "saltar",
    set: "serie",
    weight: "peso (kg)",
    reps: "reps",
    setsProgress: (done: number, total: number) => `${done} de ${total} series`,
    offline: "sin conexión · se guardará al recuperar red",
  },
  substitutions: {
    title: "alternativas",
    empty: "no hay alternativas para este patrón",
    oftenSwap: "sustituyes esto a menudo · plantéate cambiarlo en la rutina",
  },
  units: {
    kg: "kg",
  },
} as const;

export type Strings = typeof es;
