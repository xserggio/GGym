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
    remember: "recordar contraseña en este dispositivo",
  },
  today: {
    now: "toca ahora",
    treadmill: "cinta",
    treadmillStart: "empezar",
    treadmillStop: "parar",
    kcal: (n: number) => `${n} kcal aprox.`,
    bodyweight: "peso corporal",
    weekAverage: "kg · media de la semana",
    vsPrevious: "frente a la anterior",
    logWeight: "registrar peso",
    save: "guardar",
    noData: "—",
    session: "sesión",
    exercises: "ejercicios",
    sets: "series",
    perSide: "por pierna",
    skip: "saltar esta sesión",
    recovery:
      "llevas tres días seguidos entrenando. descansar también forma parte del plan.",
    resume:
      "llevas más de diez días sin entrenar. bajamos los pesos un 10% para retomar.",
  },
  session: {
    rest: "descanso",
    addFifteen: "+15",
    skipRest: "saltar",
    set: "serie",
    weight: "peso (kg)",
    reps: "reps",
    setsProgress: (done: number, total: number) => `${done} de ${total} series`,
    offline: "cambios sin sincronizar · se guardan al recuperar red",
    progressionHint: (sets: number, reps: number, bumpKg: string) =>
      `la última vez completaste las ${sets} series a ${reps} repeticiones. prueba con ${bumpKg} kg más.`,
    insteadOf: (name: string) => `en lugar de ${name}`,
    notesLabel: "notas de la sesión",
    notesPlaceholder: "dolor, sueño, energía…",
  },
  detail: {
    photoNote: "foto 4:3 · duotono tinta/cemento",
    weightHistory: "historial de pesos",
    empty: "aún no has registrado este ejercicio",
    viewExercise: "ver ejercicio",
    pr: "pr",
  },
  substitutions: {
    title: "alternativas",
    empty: "no hay alternativas para este patrón",
    oftenSwap: "sustituyes esto a menudo · plantéate cambiarlo en la rutina",
  },
  nav: {
    today: "hoy",
    history: "historial",
    routine: "rutina",
  },
  routine: {
    title: "rutina",
    hint: "cinco sesiones en rueda. usa las flechas para reordenar.",
    sets: "series",
    reps: "reps",
    rest: "descanso",
    add: "añadir ejercicio",
    addTitle: "añadir ejercicio",
    remove: "quitar",
    empty: "sesión sin ejercicios",
  },
  settings: {
    title: "ajustes",
    profile: "perfil",
    appearance: "apariencia",
    light: "clara",
    dark: "oscura",
    export: "exportar datos (json)",
    exporting: "exportando…",
    logout: "salir",
  },
  history: {
    title: "historial",
    empty:
      "aún no hay sesiones registradas. la primera aparecerá aquí en cuanto termines una.",
    adherence: "adherencia · últimas 4 semanas",
    sessionsIn4w: (n: number) => `${n} sesiones · 4 semanas`,
    volume: "volumen semanal · series por grupo",
    volumeHint: "rango útil 10-20",
    records: "récords · mejor 1rm estimado",
    sessions: "sesiones",
    bodyweight: "peso corporal · media móvil 7 días",
    minutes: (n: number) => `${n} min`,
    session: "sesión",
    loading: "cargando…",
  },
  units: {
    kg: "kg",
  },
} as const;

export type Strings = typeof es;
