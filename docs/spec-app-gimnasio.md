# App de gimnasio — especificación técnica

Documento de contexto para construir la aplicación con Claude Code. Autocontenido: incluye modelo de datos, reglas de negocio, rutina precargada y plan de despliegue.

---

## 1. Objetivo

Aplicación web instalable en el móvil para gestionar sesiones de entrenamiento de fuerza. Multiusuario (dos perfiles reales de inicio, arquitectura preparada para más). Datos en servidor propio (VPS). Debe funcionar dentro de un gimnasio, es decir: **con cobertura mala o nula**.

No es una app de nutrición. No cuenta calorías ni alimentos.

---

## 2. Stack

| Capa | Elección | Motivo |
|---|---|---|
| Backend | FastAPI (Python 3.12) | Stack conocido, tipado con Pydantic, OpenAPI gratis |
| Base de datos | SQLite con WAL | Dos usuarios; un fichero, backup trivial. Migrar a Postgres solo si crece |
| ORM / migraciones | SQLAlchemy 2.0 + Alembic | Cambios de esquema controlados |
| Frontend | React 18 + Vite + TypeScript + Tailwind | PWA instalable |
| Offline | IndexedDB (Dexie) + cola de sincronización | Requisito duro: el sótano del gimnasio no tiene cobertura |
| PWA | `vite-plugin-pwa` (Workbox) | Service worker, instalable, icono en el escritorio |
| Auth | JWT en cookie httpOnly, contraseña con Argon2 | Sin registro público: usuarios sembrados a mano |
| Despliegue | Docker Compose: `api` + `caddy` | Caddy da HTTPS automático con Let's Encrypt |
| Backups | `cron` → copia del `.db` + `rclone` a almacenamiento remoto | El histórico de entrenos es irrecuperable si se pierde |

**Sin registro abierto.** Un comando de CLI (`python -m app.cli create-user`) crea perfiles. Es una app para dos personas expuesta a internet: cualquier formulario de alta es superficie de ataque innecesaria.

---

## 3. Decisión de arquitectura central: log de eventos append-only

Todo lo que el usuario registra durante una sesión (series, sustituciones, notas) es un **evento inmutable con UUID generado en el cliente**.

Consecuencias:

- La sincronización es idempotente: reenviar un evento ya recibido no hace nada (`INSERT OR IGNORE` por UUID).
- No hay conflictos de merge. No hace falta lógica de resolución.
- El cliente puede trabajar horas sin red y volcarlo todo al salir del gimnasio.
- El histórico es auditable: nunca se sobrescribe una serie, se anula con un evento de corrección.

Endpoint de sincronización único: `POST /sync` recibe un array de eventos y devuelve los eventos del servidor posteriores a un cursor. El cliente reconstruye el estado.

---

## 4. Modelo de datos

### Catálogo (compartido entre usuarios)

```
exercises
  id              uuid pk
  name            text            -- "Press banca"
  pattern         text            -- ver enum de patrones abajo
  equipment       text            -- barra | mancuernas | maquina | polea | peso_corporal
  description     text            -- explicación en lenguaje llano, se muestra al tocar el ejercicio
  media_url       text nullable   -- imagen o gif de la ejecución
  default_rest_s  int             -- 90 accesorios, 120 pesados
```

**Enum de patrones** (`pattern`) — es la clave de las sustituciones:

`empuje_horizontal`, `empuje_vertical`, `tiron_horizontal`, `tiron_vertical`,
`cuadriceps`, `cadena_posterior`, `gluteo`, `gemelo`,
`deltoides_lateral`, `triceps`, `biceps`, `core`

### Rutinas

```
routines
  id, user_id, name, active bool

routine_days                       -- las "sesiones 1..5"
  id, routine_id
  position        int              -- 1..N, orden de la rueda
  name            text             -- "Torso (fuerza)"
  suggested_dow   int nullable     -- día sugerido, solo informativo

routine_day_exercises
  id, routine_day_id, exercise_id
  order_index     int
  target_sets     int
  rep_min         int
  rep_max         int
  rest_s          int nullable     -- si null, usa default del ejercicio
```

### Estado y registro

```
user_state
  user_id pk
  routine_id
  next_position   int              -- EL PUNTERO DE LA RUEDA
  last_session_at timestamp

sessions
  id uuid pk, user_id, routine_day_id
  started_at, ended_at
  status          text             -- in_progress | completed | abandoned
  notes           text nullable

set_logs                           -- append-only
  id uuid pk, session_id
  exercise_id                      -- el realmente ejecutado
  planned_exercise_id nullable     -- el que tocaba, si hubo sustitución
  set_number      int
  weight_kg       numeric
  reps            int
  voided          bool default false
  created_at

body_weights
  id uuid pk, user_id, measured_on date, weight_kg numeric

treadmill_sessions
  id uuid pk, user_id, started_at, ended_at, duration_s int

exercise_preferences               -- sustituciones que se vuelven permanentes
  user_id, planned_exercise_id, preferred_exercise_id, substitution_count
```

---

## 5. Reglas de negocio

### 5.1 La rueda

El puntero `next_position` **solo avanza cuando una sesión se marca como completada**. No depende del calendario.

- Si toca la sesión 2 y no va el martes, el jueves que vaya le toca la sesión 2.
- Al completar la última posición, vuelve a 1.
- Los días de descanso **no son posiciones**: son simplemente días en los que no se abre sesión.
- `suggested_dow` sirve solo para la notificación diaria y para pintar el calendario sugerido en gris.

Botón **"Saltar esta sesión"**: avanza el puntero sin registrar sesión. Para cuando quiere ir pero prefiere cambiar de bloque.

**Aviso de recuperación** (no bloqueante): si hay 3 sesiones completadas en 3 días naturales consecutivos, mostrar un aviso al iniciar la cuarta. Un músculo entrenado necesita 48-72 h; la rueda no lo garantiza sola.

**Reanudación tras parón**: si `last_session_at` tiene más de 10 días, sugerir los pesos de la última sesión menos un 10%.

### 5.2 Progresión automática

Al abrir un ejercicio, mostrar el registro de la última sesión en la que se hizo.

Regla de subida: si en la última sesión **todas** las series alcanzaron `rep_max`, sugerir para hoy:
- `+2,5 kg` si el patrón es de tren superior
- `+5 kg` si es `cuadriceps` o `cadena_posterior`

Si no, repetir el peso anterior. La sugerencia es un valor precargado en el input, editable siempre.

### 5.3 Sustituciones ("máquina ocupada")

Botón en cada ejercicio. Al pulsarlo, lista los ejercicios del catálogo con el **mismo `pattern`**, ordenados por los que ya haya usado antes. El criterio es el patrón de movimiento, no el músculo.

Se registra en `set_logs.planned_exercise_id` para no falsear el histórico de progresión.

Cuando `substitution_count` para un par llega a 3, ofrecer: *"Sustituyes X por Y a menudo. ¿Lo cambiamos en la rutina?"* Si la máquina siempre está ocupada a su hora, el problema es la rutina, no el día.

### 5.4 Descanso

Cronómetro que arranca solo al registrar una serie, con el valor de `rest_s` del ejercicio. Editable sobre la marcha.

**Aviso de implementación**: los temporizadores en segundo plano son poco fiables en PWA, especialmente en iOS. No confiar en `setTimeout` con la pantalla apagada. Programar una notificación local con timestamp absoluto y, además, recalcular el tiempo restante a partir de `Date.now()` cada vez que la app vuelve a primer plano. Vibración con `navigator.vibrate` donde esté disponible.

### 5.5 Cinta

Cronómetro `start / stop / reset` independiente de las sesiones de fuerza. Guarda duración. Estimación de gasto: `duración_min × 0,053 × peso_kg` (equivale a ~3 MET caminando a 4 km/h). El peso sale del último registro de `body_weights`.

### 5.6 Peso corporal

Un registro por semana basta. Mostrar **media móvil de 7 días**, nunca el valor crudo: el peso diario oscila un par de kilos por agua y no significa nada. La tendencia es el único dato accionable.

---

## 6. Pantallas

1. **Hoy** — pantalla de inicio. Tarjeta grande con la sesión que toca según el puntero, botón "Empezar". Debajo: cronómetro de cinta y acceso al peso semanal.
2. **Sesión activa** — lista de ejercicios, cada uno desplegable con sus series. Por serie: peso, reps, check. Cronómetro de descanso flotante. Botón de sustitución por ejercicio. Botón "Terminar sesión".
3. **Ejercicio** — nombre, imagen/gif, descripción en lenguaje llano, historial de pesos.
4. **Historial** — sesiones pasadas, adherencia de las últimas 4 semanas, gráfica de peso corporal.
5. **Rutina** — ver y editar las 5 sesiones y sus ejercicios.
6. **Ajustes** — perfil, tiempos de descanso por defecto, exportar todo a JSON.

Diseño mobile-first con objetivos táctiles grandes: se usa de pie, con prisa y con las manos sudadas. Los inputs de peso y reps deben ser pulsables (`+`/`−` con incrementos de 2,5 kg y 1 rep), no solo teclado numérico.

---

## 7. Funcionalidades adicionales recomendadas

Priorizadas. Las tres primeras aportan más que cualquier refinamiento visual.

1. **Volumen semanal por grupo muscular** — series efectivas por músculo en los últimos 7 días. Es el único diagnóstico real de si la rutina está equilibrada; el rango útil es 10-20 series semanales por grupo.
2. **Récords personales** — mejor peso por ejercicio y estimación de 1RM (fórmula de Epley: `peso × (1 + reps/30)`). Es el refuerzo psicológico honesto, frente a las rachas artificiales.
3. **Exportación a JSON** — desde ajustes, sin depender del backup del servidor.
4. **Modo sesión corta** — marca los 3 ejercicios prioritarios de la sesión y oculta los accesorios. Para los días de 25 minutos, que existen y de otro modo se convierten en días de cero.
5. **Notas por sesión** — dolor, sueño, energía. Texto libre, sin escalas.
6. **Notificación diaria** a la hora habitual de entreno. La adherencia es el cuello de botella declarado.
7. **API de lectura pública con token** — `GET /api/public/today?token=…` devolviendo JSON con la sesión del día y la adherencia. Pensado para que la pantalla de tinta electrónica lo consuma sin autenticación completa.

---

## 8. Rutina precargada (seed)

Upper / Lower / Push / Pull / Legs. Descanso entre bloques.

### Sesión 1 — Torso (fuerza) · sugerido lunes
| Ejercicio | Patrón | Series × reps |
|---|---|---|
| Press banca | empuje_horizontal | 4 × 6-8 |
| Remo con barra | tiron_horizontal | 4 × 8-10 |
| Press militar de pie | empuje_vertical | 3 × 8 |
| Jalón agarre neutro | tiron_vertical | 3 × 10 |
| Elevaciones laterales en polea | deltoides_lateral | 3 × 15 |

### Sesión 2 — Pierna (fuerza) · sugerido martes
| Ejercicio | Patrón | Series × reps |
|---|---|---|
| Sentadilla | cuadriceps | 4 × 5-8 |
| Peso muerto rumano | cadena_posterior | 3 × 8-10 |
| Prensa | cuadriceps | 3 × 12 |
| Curl femoral tumbado | cadena_posterior | 3 × 12 |
| Gemelos de pie | gemelo | 4 × 12 |
| Rueda abdominal | core | 3 × 10 |

### Sesión 3 — Empuje · sugerido jueves
| Ejercicio | Patrón | Series × reps |
|---|---|---|
| Press inclinado con mancuernas | empuje_horizontal | 4 × 8-10 |
| Press de hombro en máquina | empuje_vertical | 3 × 10 |
| Cruces en polea | empuje_horizontal | 3 × 15 |
| Elevaciones laterales con mancuernas | deltoides_lateral | 3 × 15 |
| Tríceps en polea | triceps | 3 × 12 |

### Sesión 4 — Tirón · sugerido viernes
| Ejercicio | Patrón | Series × reps |
|---|---|---|
| Dominadas | tiron_vertical | 4 × 8 |
| Remo sentado en polea | tiron_horizontal | 4 × 10 |
| Remo en máquina con pecho apoyado | tiron_horizontal | 3 × 12 |
| Face pull | tiron_horizontal | 3 × 15 |
| Curl con barra Z | biceps | 3 × 10 |
| Curl martillo | biceps | 2 × 12 |

### Sesión 5 — Pierna (hipertrofia) · sugerido sábado
| Ejercicio | Patrón | Series × reps |
|---|---|---|
| Hack squat | cuadriceps | 4 × 10-12 |
| Hip thrust | gluteo | 3 × 10 |
| Sentadilla búlgara | cuadriceps | 3 × 10 por pierna |
| Extensión de cuádriceps | cuadriceps | 3 × 15 |
| Curl femoral sentado | cadena_posterior | 3 × 12 |

### Alternativas para el catálogo (alimentan las sustituciones)

- `empuje_horizontal`: press banca con mancuernas, press en máquina, fondos en paralelas, pec deck
- `empuje_vertical`: press militar con mancuernas, press Arnold, press en máquina
- `tiron_horizontal`: remo T, remo con mancuerna a una mano, remo en máquina, remo en polea agarre ancho
- `tiron_vertical`: jalón agarre ancho, dominadas asistidas, pullover en polea
- `cuadriceps`: sentadilla frontal, sentadilla en multipower, zancadas caminando, sentadilla goblet
- `cadena_posterior`: peso muerto rumano con mancuernas, buenos días, curl femoral de pie, hiperextensiones
- `gluteo`: hip thrust en máquina, patada de glúteo en polea, puente de glúteo
- `triceps`: press francés, fondos en banco, extensión sobre la cabeza en polea
- `biceps`: curl con mancuernas, curl en banco inclinado, curl en polea baja
- `core`: elevaciones de piernas colgado, plancha, crunch en polea

---

## 9. Orden de construcción sugerido

1. Esquema, migraciones y CLI de creación de usuarios.
2. Seed del catálogo de ejercicios y de la rutina de arriba.
3. API: auth, `/sync`, endpoints de lectura.
4. Frontend: pantalla Hoy + sesión activa + registro de series. **Esto ya es usable en el gimnasio.**
5. Cronómetro de descanso y sustituciones.
6. Cinta y peso corporal.
7. Historial, volumen semanal y PRs.
8. Offline: cola en IndexedDB y service worker.
9. Docker Compose, Caddy, backups.

Los pasos 1-4 son la aplicación mínima que aporta valor. Todo lo demás es mejora sobre algo que ya funciona.

---

## 10. Decisiones abiertas

- Qué corre ya en el VPS (Docker, reverse proxy existente, dominio o subdominio disponible).
- Si el catálogo de ejercicios lleva imágenes propias o enlaces externos. Enlaces externos se rompen; imágenes propias hay que subirlas una vez. Recomendado: propias, en `/static/exercises/`.
- Si la pareja usa la misma rutina o una distinta. El modelo lo soporta desde el principio, pero el seed inicial cambia.
