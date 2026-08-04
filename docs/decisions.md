# Decisiones de diseño

Registro de resoluciones cuando la spec y el prototipo de Claude Design se
contradicen (CLAUDE.md: "Si ambos se contradicen, pregunta antes de decidir").

## D1 — "Semana N del bloque": derivada, sin tabla
- **Contexto**: el prototipo muestra "semana 12 del bloque" en la cabecera de
  inicio; la spec no define mesociclos.
- **Decisión**: no se modela como tabla. Se deriva del calendario de sesiones
  (primera sesión del ciclo). Cero cambios de esquema.

## D2 — Volumen: se guardan datos para ambas métricas
- **Contexto**: la spec define volumen como "series efectivas por grupo muscular"
  (10-20/sem); el dashboard del prototipo muestra tonelaje (18,4 t).
- **Decisión**: ambas se derivan de `set_logs` (tonelaje = Σ `weight_kg × reps`;
  series efectivas = recuento por `exercise.pattern`). El dashboard usa tonelaje
  como cifra rápida; la pantalla de volumen usa series efectivas. Sin esquema nuevo.

## D3 — Rutina: una copia por usuario
- **Contexto**: la spec dice que el modelo soporta rutina distinta por usuario,
  pero el seed depende de la elección.
- **Decisión**: el seed crea una copia de las 5 sesiones por usuario
  (`routines.user_id`). Editables por separado.

## D4 — `/sync`: outbox con cursor entero monotónico
- **Contexto**: la spec §3 pide que `POST /sync` reciba eventos y devuelva "los
  eventos del servidor posteriores a un cursor", sin definir el mecanismo.
- **Decisión**: una tabla append-only `sync_events` (`seq` INTEGER PK = rowid
  monotónico) actúa de log de salida. El cursor del cliente es el último `seq`
  visto; el servidor devuelve `seq > cursor` del propio usuario. La idempotencia
  vive en las tablas tipadas: un evento reenviado que no cambia nada no añade
  fila al outbox. Alcance por `/sync`: `sessions`, `set_logs`, `body_weights`,
  `treadmill_sessions`. Rutina y `exercise_preferences` van por endpoints normales.

## D5 — `set_logs`: anulación como única mutación permitida
- **Contexto**: la regla 1 (append-only) dice "nunca UPDATE sobre una serie; se
  anula con `voided=true` y se inserta la corrección", pero `voided` es una
  columna que hay que cambiar.
- **Decisión**: `set_logs` es insert-only salvo una transición monotónica
  `voided` false→true, que es idempotente y sin conflictos de merge (preserva el
  espíritu append-only). La corrección es una fila nueva con otro UUID. El avance
  de la rueda en `sessions` ocurre solo en la primera transición a `completed`.

## Nota de entorno
- La spec fija Python 3.12; la máquina de desarrollo solo tiene 3.13.7.
  Se usa 3.13 (compatible con todo el stack) y `requires-python = ">=3.12"`.
