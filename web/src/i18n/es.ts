/**
 * Every user-visible string, in español de España. No loose literals in
 * components (CLAUDE.md). Voice: sentence-case, active verbs, no exclamation
 * marks, no emojis.
 */
export const es = {
  app: {
    title: "registro de fuerza",
    brand: "GGym",
  },
  actions: {
    start: "empezar",
    endSession: "terminar sesión",
    busy: "ocupada",
    skipSession: "saltar esta sesión",
    viewExercise: "ver ejercicio",
    settings: "ajustes",
    back: "volver",
    continue: "continuar",
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
    wheel: "rueda",
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
    completed: "completado",
  },
  highlights: {
    title: "sesión completada",
    duration: "duración",
    volume: "peso levantado",
    sets: "series",
    kcal: "calorías",
    approx: "aprox.",
    min: "min",
    done: "hecho",
    bestSet: "mejor serie",
  },
  detail: {
    technique: "cómo hacerlo",
    mistakes: "errores a evitar",
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
  // Backend enum values are snake_case ids; never show them raw.
  patterns: {
    empuje_horizontal: "empuje horizontal",
    empuje_vertical: "empuje vertical",
    tiron_horizontal: "tirón horizontal",
    tiron_vertical: "tirón vertical",
    cuadriceps: "cuádriceps",
    cadena_posterior: "cadena posterior",
    gluteo: "glúteo",
    gemelo: "gemelo",
    deltoides_lateral: "deltoides lateral",
    triceps: "tríceps",
    biceps: "bíceps",
    core: "core",
    abduccion: "abducción",
  } as Record<string, string>,
  equipment: {
    barra: "barra",
    mancuernas: "mancuernas",
    maquina: "máquina",
    polea: "polea",
    peso_corporal: "peso corporal",
    banda: "banda",
  } as Record<string, string>,
  nav: {
    today: "hoy",
    history: "historial",
    routine: "rutina",
    home: "inicio",
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
  periods: {
    "7d": "7 días",
    "30d": "1 mes",
    "365d": "1 año",
    all: "todo",
  } as Record<string, string>,
  milestones: {
    title: "mejores marcas",
    empty: "aún no hay marcas: registra alguna sesión",
    heaviest_set: "serie más pesada",
    longest_session: "sesión más larga",
    best_session_volume: "más peso en una sesión",
    longest_run: "más tiempo en cinta",
  } as Record<string, string>,
  home: {
    title: "inicio",
    week: "resumen",
    nextUp: "lo siguiente",
    sessions: "sesiones",
    sets: "series",
    volume: "peso levantado",
    kcal: "calorías",
    kcalHint: "registra tu peso para estimar calorías",
    time: "tiempo entrenando",
    treadmill: "cinta",
    bodyweight: "peso corporal",
    trend: "media de 7 días",
    noWeight: "sin registrar",
    balance: "series por grupo muscular",
    balanceHint:
      "series efectivas de cada patrón en el periodo. lo saludable es 10-20 por grupo a la semana: menos se queda corto, más suele ser exceso.",
    records: "récords por ejercicio",
    noRecords: "aún no hay récords",
    lastSession: (d: string) => `último entreno: ${d}`,
    neverTrained: "aún no has entrenado",
    start: "empezar sesión",
    detail: "ver detalle",
    vsPrev: "frente al periodo anterior",
    firstTime: "aún no has registrado nada",
    firstTimeHint:
      "en cuanto termines tu primera sesión, aquí verás el trabajo por grupo muscular, tus mejores marcas y los récords de cada ejercicio.",
  },
  treadmillScreen: {
    title: "cinta",
    start: "empezar",
    pause: "pausar",
    resume: "reanudar",
    stop: "terminar y guardar",
    running: "en marcha",
    paused: "en pausa",
    weekTotal: "esta semana",
    allTime: "total acumulado",
    history: "historial",
    empty: "todavía no has usado la cinta",
    kcalHint: "las calorías necesitan tu peso corporal registrado",
    pausedNote: "el tiempo en pausa no cuenta",
  },
  weightScreen: {
    title: "peso corporal",
    current: "media de 7 días",
    latest: "última medida",
    delta: "frente a la semana anterior",
    history: "historial",
    empty: "todavía no has registrado tu peso",
    add: "registrar peso de hoy",
    hint: "la media móvil es el único dato fiable: el peso diario oscila por agua",
  },
  phases: {
    title: "fases",
    open: "gestionar fases",
    enable: "seguir fases de volumen y definición",
    explain:
      "declaras en qué fase estás y la app comprueba si tu peso se mueve al ritmo que corresponde. no calcula calorías: eso depende de lo que comas, y la app no lo sabe.",
    off: "activa las fases en ajustes para usarlas",
    none: "sin fase activa",
    noneHint: "elige una para que la app adapte la progresión y vigile tu ritmo",
    start: "empezar fase",
    end: "terminar fase",
    change: "cambiar de fase",
    week: (n: number) => (n < 1 ? "primera semana" : `semana ${Math.floor(n) + 1}`),
    target: "objetivo",
    actual: "real",
    perWeek: "%/semana",
    history: "fases anteriores",
    noHistory: "aún no has cerrado ninguna fase",
    rate: "ritmo objetivo",
    targetDate: "fecha objetivo (opcional)",
    kinds: {
      superavit: "superávit",
      definicion: "definición",
      mantenimiento: "mantenimiento",
    } as Record<string, string>,
    kindHints: {
      superavit: "ganar músculo con una subida lenta de peso",
      definicion: "bajar grasa manteniendo la fuerza",
      mantenimiento: "sostener el peso mientras entrenas",
    } as Record<string, string>,
    verdicts: {
      en_rumbo: "vas en rumbo",
      demasiado_rapido: "vas más rápido de lo previsto",
      demasiado_lento: "vas más lento de lo previsto",
      subiendo: "estás subiendo de peso",
      bajando: "estás bajando de peso",
      sin_datos: "faltan pesajes para valorar el ritmo",
    } as Record<string, string>,
    verdictHints: {
      demasiado_rapido:
        "perder peso muy rápido cuesta músculo; bajar más lento suele conservar más fuerza",
      demasiado_lento: "el peso apenas se mueve en la dirección que buscabas",
      sin_datos: "hacen falta al menos tres pesajes repartidos en dos semanas",
    } as Record<string, string>,
    duration: {
      larga:
        "llevas bastantes semanas en esta fase. plantéate pasar a mantenimiento una temporada.",
      muy_larga:
        "esta fase se ha alargado mucho. un periodo en mantenimiento ayuda al descanso, al sueño y al rendimiento.",
    } as Record<string, string>,
    holdingLoad:
      "en definición la app no te propone subir peso: mantener la carga ya es ganar.",
    daysToTarget: (n: number) => `faltan ${n} días para tu fecha objetivo`,
    confirmEnd: "se cerrará la fase actual y quedará en el historial.",
    advise: "ayúdame a elegir",
    assessTitle: "evaluación",
    assessOpen: "hacer una evaluación",
    assessIntro:
      "siete preguntas para proponerte qué fase encaja mejor ahora, a qué ritmo y durante cuánto. puedes usarlo como plantilla o ignorarlo.",
    assessResult: "lo que te propongo",
    assessApply: "usar como plantilla",
    assessRedo: "volver a empezar",
    assessWeeks: (n: number) => `durante unas ${n} semanas`,
    assessStep: (n: number, total: number) =>
      `${String(n).padStart(2, "0")} / ${String(total).padStart(2, "0")}`,
    assessPrev: "anterior",
    assessAnswers: "tus respuestas",
    assessEdit: "cambiar",
    assessWhy: "por qué",
    assessRate: "ritmo",
    assessDuration: "duración",
    assessNoRate: "sin subir ni bajar",
    assessDisclaimer:
      "esto es una guía a partir de lo que has contado, no un consejo médico. tú decides.",
    questions: {
      objetivo: "¿qué buscas ahora mismo?",
      grasa: "¿cómo estás de grasa corporal?",
      experiencia: "¿cuánto llevas entrenando de forma constante?",
      dieta_reciente: "¿cómo has comido en los últimos meses?",
      fecha: "¿tienes una fecha en mente?",
      prioridad: "si tuvieras que elegir…",
      energia: "¿qué tal de energía, sueño y descanso?",
    } as Record<string, string>,
    options: {
      objetivo: {
        ganar_musculo: "ganar músculo",
        bajar_grasa: "bajar grasa",
        mantener_rendir: "mantenerme y rendir en el gym",
      },
      grasa: {
        muy_alta: "hay bastante que perder",
        alta: "por encima de donde me gustaría",
        media: "en un punto intermedio",
        baja: "se me intuye el abdomen",
        muy_baja: "se me marca claramente",
      },
      experiencia: {
        menos_6m: "menos de seis meses",
        "6m_1a": "entre seis meses y un año",
        "1_3a": "entre uno y tres años",
        "3_5a": "entre tres y cinco años",
        mas_5a: "más de cinco años",
      },
      dieta_reciente: {
        meses_deficit: "llevo meses comiendo por debajo",
        vengo_de_volumen: "vengo de una etapa comiendo de más",
        nada_especial: "nada especial, normal",
      },
      fecha: {
        hay_fecha: "sí, tengo una fecha",
        sin_prisa: "no, sin prisa",
      },
      prioridad: {
        fuerza: "seguir subiendo fuerza",
        estetica: "verme mejor",
        equilibrio: "un equilibrio de ambas",
      },
      energia: {
        bien: "bien, descanso y tengo energía",
        regular: "regular, voy tirando",
        mal: "mal, duermo poco o estoy quemada",
      },
    } as Record<string, Record<string, string>>,
    reasons: {
      descanso_tras_deficit:
        "llevas meses en déficit: antes de seguir, un tiempo en mantenimiento recupera hormonas, sueño y rendimiento, y hace que el siguiente déficit funcione mejor",
      energia_baja:
        "con el descanso justo, un déficit se lleva por delante la fuerza y la adherencia; primero recuperar",
      energia_baja_volumen:
        "descansando poco no vas a bajar bien, pero sí puedes construir: mantengo el volumen y lo hago más lento, porque el músculo se hace descansando",
      bajar_antes_de_ganar:
        "partiendo de bastante grasa, comer de más añade sobre todo grasa: bajar primero hace que el volumen posterior cunda mucho más",
      ya_muy_definida:
        "estando ya muy definida, seguir bajando cuesta músculo y salud hormonal más que grasa",
      vienes_de_volumen:
        "vienes de una etapa comiendo de más: encadenar otra suele acabar en un volumen largo y sucio; bajar antes deja sitio para ganar de nuevo",
      objetivo_ganar: "buscas músculo y tu punto de partida lo permite",
      objetivo_bajar: "buscas bajar grasa y hay margen para hacerlo",
      objetivo_mantener: "quieres sostener y rendir",
      ritmo_por_grasa_muy_alta: "con grasa de sobra puedes bajar rápido sin perder músculo",
      ritmo_por_grasa_alta: "hay margen para un déficit decidido",
      ritmo_por_grasa_media: "un ritmo intermedio conserva la fuerza",
      ritmo_por_grasa_baja: "estando fina conviene bajar despacio",
      ritmo_por_grasa_muy_baja: "a este nivel, lo más lento posible",
      ritmo_por_experiencia_menos_6m: "empezando se gana rápido",
      ritmo_por_experiencia_6m_1a: "aún estás en la parte fácil de la curva",
      "ritmo_por_experiencia_1_3a": "con recorrido, subir despacio evita grasa de más",
      "ritmo_por_experiencia_3_5a": "el músculo ya llega lento",
      ritmo_por_experiencia_mas_5a: "a estas alturas, muy despacio: lo demás es grasa",
      suavizado_energia: "he bajado el ritmo porque no vas sobrada de descanso",
      suavizado_energia_mal: "y lo he bajado bastante: sin descanso, subir rápido es subir grasa",
      suavizado_fuerza: "he bajado el ritmo para proteger la fuerza",
      suavizado_estetica: "he bajado el ritmo para que la subida sea más limpia",
      con_fecha: "tienes fecha: contrasta abajo si el peso que quieres cabe en ella",
    } as Record<string, string>,
    trainingAge: "¿cuánto llevas entrenando de forma constante?",
    fatLevel: "¿cómo dirías que estás ahora?",
    trainingAges: {
      menos_1: "menos de un año",
      "1_3": "entre uno y tres años",
      mas_3: "más de tres años",
    } as Record<string, string>,
    fatLevels: {
      alta: "con bastante grasa que perder",
      media: "en un punto intermedio",
      baja: "ya bastante definida",
    } as Record<string, string>,
    rationales: {
      superavit_menos_1:
        "empezando se gana músculo rápido, así que puedes permitirte subir algo más",
      superavit_1_3: "con algo de recorrido, subir despacio evita acumular grasa de más",
      superavit_mas_3:
        "con años de entrenamiento el músculo llega muy despacio: subir más rápido solo añade grasa",
      definicion_alta: "con grasa de sobra puedes bajar más rápido sin perder músculo",
      definicion_media: "un ritmo intermedio conserva la fuerza mientras bajas",
      definicion_baja:
        "estando ya definida, un déficit agresivo se lleva músculo: mejor ir despacio",
      mantenimiento: "el objetivo es sostener el peso",
    } as Record<string, string>,
    recommended: "recomendado",
    useRecommended: "usar el recomendado",
    targetWeight: "peso objetivo (opcional)",
    feasibility: "contraste con tu fecha",
    feasible: (weeks: number) =>
      `alcanzable: en ${weeks} semanas da tiempo de sobra al ritmo previsto`,
    tooDemanding: (required: string, cap: string, reachable: string, weeks: number) =>
      `eso exigiría ${required} %/semana, por encima del máximo saludable (${cap} %). A ese máximo llegarías a ${reachable} kg en la fecha, o necesitarías unas ${weeks} semanas para llegar al peso que quieres.`,
    wrongDirection: "ese peso objetivo va en dirección contraria a la fase elegida",
    needWeight: "registra tu peso para poder contrastar la fecha",
  },
  profiles: {
    open: "perfiles y copia de seguridad",
    title: "perfiles de rutina",
    hint: "prueba cambios sin miedo: nada se borra al cambiar de perfil ni al restaurar.",
    inUse: "en uso",
    original: "original",
    originalHint: "copia intacta de tu rutina inicial. no se edita ni se borra.",
    days: (n: number) => (n === 1 ? "1 sesión" : `${n} sesiones`),
    trained: (n: number) => (n === 1 ? "1 entreno" : `${n} entrenos`),
    use: "usar",
    duplicate: "duplicar",
    rename: "renombrar",
    delete: "borrar",
    restore: "volver a la rutina original",
    restoreConfirm:
      "se activará una copia de tu rutina original. la que usas ahora se guarda como perfil, no se pierde.",
    deleteConfirm: "se borrará este perfil. no se puede deshacer.",
    deleteBlocked: "no se puede borrar: tiene entrenos registrados o está en uso",
    copyName: (name: string) => `${name} (copia)`,
    namePrompt: "nombre del perfil",
    confirm: "confirmar",
    cancel: "cancelar",
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
  notifications: {
    title: "recordatorio diario",
    enable: "avisarme a la hora de entrenar",
    time: "hora",
    explain: "solo los días que toca sesión, y nunca si ya has entrenado ese día",
    devices: (n: number) =>
      n === 1 ? "1 dispositivo activado" : `${n} dispositivos activados`,
    denied: "has bloqueado las notificaciones en este navegador; actívalas en sus ajustes",
    unsupported: "este navegador no admite notificaciones",
    installFirst: "en iphone, instala la app en la pantalla de inicio para recibir avisos",
    unavailable: "el servidor no tiene las notificaciones configuradas",
    saving: "guardando…",
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
  assistant: {
    title: "asistente",
    open: "revisar mi rutina",
    intro:
      "cinco preguntas, y el resto lo miro yo: tu rutina, tus series y tus sustituciones ya están aquí. después te digo qué cambiaría y dónde, y decides tú.",
    step: (n: number, total: number) =>
      `${String(n).padStart(2, "0")} / ${String(total).padStart(2, "0")}`,
    prev: "anterior",
    analysing: "mirando tu rutina…",
    questions: {
      dias: "¿cuántos días a la semana quieres entrenar?",
      tiempo: "¿cuánto tiempo tienes por sesión?",
      objetivo: "¿qué buscas al entrenar?",
      prioridad: "¿hay algo que quieras trabajar más?",
      evitar: "¿hay algo que te dé molestias?",
    } as Record<string, string>,
    options: {
      dias: {
        "2": "dos días",
        "3": "tres días",
        "4": "cuatro días",
        "5": "cinco días",
        "6": "seis días",
      },
      tiempo: {
        "45": "unos 45 minutos",
        "60": "una hora",
        "75": "hora y cuarto",
        "90": "hora y media o más",
      },
      objetivo: {
        fuerza: "levantar más peso",
        hipertrofia: "ganar músculo",
        equilibrio: "un equilibrio de ambas",
      },
      prioridad: {
        espalda: "espalda",
        pecho: "pecho",
        hombro: "hombro",
        gluteo: "glúteo",
        cuadriceps: "pierna",
        brazos: "brazos",
        core: "abdomen",
        nada: "nada en concreto",
      },
      evitar: {
        rodilla: "la rodilla",
        hombro: "el hombro",
        espalda_baja: "la zona lumbar",
        nada: "no, todo bien",
      },
    } as Record<string, Record<string, string>>,
    multiHint: "puedes marcar varias, o ninguna",
    muscles: {
      pecho: "pecho",
      espalda: "espalda",
      hombro: "hombro",
      biceps: "bíceps",
      triceps: "tríceps",
      cuadriceps: "cuádriceps",
      isquios: "isquios",
      gluteo: "glúteo",
      gemelo: "gemelo",
      core: "abdomen",
    } as Record<string, string>,
    bands: {
      bajo: "bajo",
      justo: "justo",
      efectivo: "en rango",
      alto: "alto",
    } as Record<string, string>,
    volumeTitle: "series efectivas por semana",
    volumeNote:
      "incluye el trabajo indirecto: un press de banca también entrena el tríceps, y contarlo aparte diría que entrenas mucho menos de lo que entrenas.",
    lengthTitle: "duración estimada",
    lengthNote: "calentamiento incluido, a tu ritmo de descansos",
    findingsTitle: "lo que cambiaría",
    noFindings:
      "no veo nada que merezca cambiarse. tu rutina cuadra con lo que me has contado.",
    severities: {
      importante: "importante",
      mejorable: "mejorable",
      detalle: "detalle",
    } as Record<string, string>,
    findings: {
      molestia: (d: Record<string, string>) =>
        `cambia ${d.exercise} por ${d.replacement} en ${d.day}`,
      volumen_bajo: (d: Record<string, string>) =>
        `sube ${d.exercise} de ${d.from} a ${d.to} series en ${d.day}`,
      volumen_prioridad: (d: Record<string, string>) =>
        `sube ${d.exercise} de ${d.from} a ${d.to} series en ${d.day}`,
      volumen_alto: (d: Record<string, string>) =>
        `baja ${d.exercise} de ${d.from} a ${d.to} series en ${d.day}`,
      volumen_ausente: (d: Record<string, string>) =>
        `no hay nada que entrene ${d.muscle} en tu rutina`,
      sesion_larga: (d: Record<string, string>) =>
        d.exercise
          ? `baja ${d.exercise} de ${d.from} a ${d.to} series en ${d.day}`
          : `${d.day} no cabe en tu tiempo`,
      orden: (d: Record<string, string>) =>
        `pon los compuestos antes que el aislamiento en ${d.day}`,
      reps: (d: Record<string, string>) =>
        `pasa ${d.exercise} a ${d.to_min}-${d.to_max} repeticiones`,
      descanso: (d: Record<string, string>) =>
        `sube el descanso de ${d.exercise} a ${d.to} segundos`,
      sustitucion: (d: Record<string, string>) =>
        `cambia ${d.exercise} por ${d.replacement} en ${d.day}`,
      nunca_registrado: (d: Record<string, string>) =>
        `quita ${d.exercise} de ${d.day}`,
      estancado: (d: Record<string, string>) =>
        `abre el rango de ${d.exercise} a ${d.to_min}-${d.to_max} repeticiones`,
      frecuencia: () => "entrenas menos días de los que te has marcado",
    } as Record<string, (d: Record<string, string>) => string>,
    why: {
      molestia: (d: Record<string, string>) =>
        `has dicho que te molesta ${d.avoid === "rodilla" ? "la rodilla" : d.avoid === "hombro" ? "el hombro" : "la zona lumbar"}. no hay que dejar el movimiento, basta con hacerlo guiado: la máquina fija el recorrido y la articulación deja de estabilizar una carga con la que ahora no está cómoda.`,
      volumen_bajo: (d: Record<string, string>) =>
        `te quedan ${d.weekly} series semanales de ${d.muscle}, contando el trabajo indirecto. por debajo de seis cuesta que un músculo crezca o se sostenga.`,
      volumen_prioridad: (d: Record<string, string>) =>
        `dijiste que querías darle más al ${d.muscle} y está en ${d.weekly} series semanales: suficiente para mantener, corto para destacarlo.`,
      volumen_alto: (d: Record<string, string>) =>
        `${d.weekly} series semanales de ${d.muscle} es más de lo que hace falta; a partir de ahí lo que se acumula es cansancio, no músculo.`,
      volumen_ausente: (d: Record<string, string>) =>
        `ningún ejercicio de tu rutina trabaja ${d.muscle} de forma directa.`,
      sesion_larga: (d: Record<string, string>) =>
        `${d.day} sale en unos ${d.minutes} minutos y me dijiste que tienes ${d.budget}. una sesión que no se termina no entrena.`,
      orden: (d: Record<string, string>) =>
        `en ${d.day} empiezas por ${d.first}. el aislamiento al principio te deja sin fuerza para lo que de verdad mueve la aguja.`,
      reps: (d: Record<string, string>) =>
        `está en ${d.from_min}-${d.from_max} repeticiones, lejos de lo que pide lo que buscas.`,
      descanso: (d: Record<string, string>) =>
        `tiene ${d.from} segundos de descanso para ser un ejercicio pesado; con tan poco, las últimas series pierden peso sin ganar nada.`,
      sustitucion: (d: Record<string, string>) =>
        `lo has cambiado por ${d.replacement} ${d.count} veces. si es lo que haces siempre, que la rutina lo diga.`,
      nunca_registrado: (d: Record<string, string>) =>
        `llevas ${d.sessions} sesiones de ${d.day} y no lo has registrado ni una vez. o lo saltas o la máquina nunca está libre; en ambos casos, ocupa sitio.`,
      estancado: (d: Record<string, string>) =>
        `llevas ${d.sessions} sesiones sin mejorar la marca. un rango más amplio te deja sumar repeticiones antes de tener que subir peso.`,
      frecuencia: (d: Record<string, string>) =>
        `en las últimas semanas has entrenado ${d.real} días por semana de los ${d.wanted} que te marcaste. no cambio nada por esto: la rutina no es lo que falla aquí.`,
    } as Record<string, (d: Record<string, string>) => string>,
    restructureTitle: "repartir en otros días",
    restructureIntro: (n: number) =>
      `entrenando ${n} días, tus cinco sesiones tardarían casi dos semanas en dar la vuelta y cada músculo se entrenaría la mitad de veces. esto reparte los mismos ejercicios en ${n} sesiones.`,
    restructureKept: (before: number, after: number) =>
      before === after
        ? `se mantienen las ${before} series, ninguna se pierde`
        : `de ${before} series se quedan ${after}`,
    restructureFits: "cabe en el tiempo que tienes",
    restructureDoesNotFit:
      "no cabe en el tiempo que has dicho. las sesiones saldrían más largas de lo que te has marcado: o le das más tiempo, o entrenas un día más.",
    restructureTrimmed: (n: number) =>
      `he quitado ${n} ${n === 1 ? "serie" : "series"}, siempre de los músculos que iban sobrados`,
    restructureUnder: (list: string) =>
      `el recorte deja por debajo de lo ideal: ${list}`,
    restructureApply: "cambiar a este reparto",
    restructureNote:
      "se crea como un perfil nuevo y tu rutina actual se queda guardada tal cual, solo que sin usar.",
    compare: "ver el cambio",
    compareTitle: "el cambio, en detalle",
    compareNow: "ahora haces",
    compareProposed: "te propongo",
    compareWhatChanges: "qué cambia",
    compareWhyTitle: "por qué",
    compareSamePattern: (pattern: string) =>
      `los dos son ${pattern}: entrenan el mismo movimiento y los mismos músculos, así que no pierdes nada de lo que ya hacías.`,
    compareEquipment: (from: string, to: string) =>
      `cambia el material: de ${from} a ${to}.`,
    compareGuided:
      "la máquina fija el recorrido, así que la articulación deja de estabilizar la carga y solo empuja. es lo que permite seguir entrenando el movimiento cuando algo molesta.",
    compareFree:
      "el peso libre te deja elegir el recorrido y trabaja más la estabilidad, a cambio de exigir más técnica.",
    compareDemandSame: "y pesa parecido, así que la sesión no se descafeína.",
    compareDemandLess:
      "es algo menos exigente, lo que a cambio te deja llevarlo mejor.",
    compareNoImage: "sin foto",
    compareClose: "cerrar",
    reviewTitle: "revisar cambios",
    snapshotNote:
      "antes de tocar nada guardo tu rutina actual como un perfil con la fecha de hoy, así que deshacer esto es un toque desde perfiles.",
    applySelected: (n: number) =>
      n === 1 ? "aplicar 1 cambio" : `aplicar ${n} cambios`,
    applyNone: "no has marcado nada",
    applied: (n: number) =>
      n === 1 ? "1 cambio aplicado" : `${n} cambios aplicados`,
    undoHint: (name: string) =>
      `tu rutina anterior está guardada como «${name}». puedes volver a ella cuando quieras desde perfiles.`,
    restructureDone: "reparto cambiado",
    restructureDoneHint: (name: string) =>
      `ahora entrenas con «${name}». la rutina que tenías sigue intacta en perfiles, solo que sin usar, así que volver a ella es un toque.`,
    changeKinds: {
      subir_series: "más series",
      bajar_series: "menos series",
      cambiar_reps: "repeticiones",
      cambiar_descanso: "descanso",
      sustituir: "cambio de ejercicio",
      quitar: "se quita",
      reordenar: "nuevo orden",
    } as Record<string, string>,
    disclaimer:
      "esto sale de tu rutina y de lo que has contestado, no de una valoración médica. si algo te duele de verdad, míralo con un profesional.",
  },
  lab: {
    title: "laboratorio",
    open: "ver laboratorio",
    recoveryTitle: "recuperación",
    recoverySub: "verde está fresco · rojo necesita descanso",
    bands: {
      cargado: "cargado",
      recuperando: "recuperando",
      fresco: "fresco",
    } as Record<string, string>,
    front: "frente",
    back: "espalda",
    overall: (n: number) => `${n} % fresco`,
    mostLoaded: (muscle: string) => `${muscle}, lo más cargado`,
    toFresh: (hours: number) =>
      hours >= 24
        ? `le quedan ~${Math.round(hours / 24)} d para estar fresco`
        : `le quedan ~${Math.round(hours)} h para estar fresco`,
    estimateNote:
      "estimado a partir de las series que registraste y del tiempo que ha pasado, no de cómo te encuentras. si algo te duele, manda tu cuerpo.",
    empty:
      "aún no has registrado ningún entrenamiento, así que no hay nada que estimar. en cuanto termines una sesión, esto se llena.",
    loadTitle: "carga reciente",
    loadSub: "esta semana frente a tu propia media",
    loadBands: {
      baja: "baja",
      equilibrada: "equilibrada",
      alta: "alta",
      excesiva: "excesiva",
    } as Record<string, string>,
    loadDetail: (acute: number, weekly: number) =>
      `${acute} series esta semana frente a ${weekly} de media en las últimas cuatro.`,
    loadNote: "subir muy rápido es la vía habitual de acabar roto.",
    loadPending:
      "hacen falta un par de semanas registradas para comparar esta semana con tu media.",
    sessionsChip: (n: number) =>
      n === 1 ? "1 sesión registrada" : `${n} sesiones registradas`,
    baselineChip: (days: number) => `línea base de ${days} días`,
    thinNote:
      "con pocas semanas registradas estos números se mueven mucho; tómatelos como un primer indicio.",
  },
  units: {
    kg: "kg",
  },
} as const;

export type Strings = typeof es;
