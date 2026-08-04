# CLAUDE.md

Contexto permanente del proyecto. Colocar en la raíz del repositorio.

---

## Qué es esto

Aplicación web instalable (PWA) para registrar entrenamientos de fuerza en el gimnasio. Dos usuarios reales con perfiles separados. Backend propio en VPS, datos en servidor.

Documentos de referencia en `/docs`:

- `spec-app-gimnasio.md` — modelo de datos, reglas de negocio y rutina precargada. **Es la fuente de verdad funcional.**
- `brief-claude-design.md` — dirección visual, paleta, tipografía y voz de la interfaz.
- `/design` — prototipo exportado de Claude Design. **Es la fuente de verdad visual.**

Ante cualquier duda funcional, gana la spec. Ante cualquier duda visual, gana el prototipo. Si ambos se contradicen, pregunta antes de decidir.

---

## Stack (cerrado, no reabrir)

- **Backend**: FastAPI, Python 3.12, SQLAlchemy 2.0, Alembic, SQLite con WAL
- **Frontend**: React 18, Vite, TypeScript estricto, Tailwind, Dexie para IndexedDB
- **PWA**: `vite-plugin-pwa`
- **Auth**: JWT en cookie httpOnly, Argon2. Sin registro público; usuarios por CLI
- **Despliegue**: Docker Compose (`api` + `caddy`)

---

## Reglas no negociables

1. **El registro de entrenamiento es append-only.** Cada `set_log` lleva un UUID generado en el cliente. Nunca se hace UPDATE sobre una serie registrada: se anula con `voided = true` y se inserta la corrección. La sincronización es idempotente por UUID.

2. **Offline primero en la sesión activa.** Registrar series funciona sin red. Se encola en IndexedDB y se sincroniza al recuperar conexión. El resto de pantallas pueden requerir red.

3. **El puntero de la rueda solo avanza al completar una sesión.** Nunca en función de la fecha. Los días de la semana son sugerencias visuales, jamás lógica.

4. **Sin registro público de usuarios.** Ningún endpoint crea cuentas. Solo `python -m app.cli create-user`.

5. **Los cronómetros se calculan con timestamps absolutos**, nunca acumulando `setInterval`. Al volver la app a primer plano, se recalcula contra `Date.now()`. Los temporizadores en segundo plano no son fiables en PWA, sobre todo en iOS.

6. **Objetivos táctiles de 44 px mínimo** en todo lo que se toque durante una sesión.

---

## Convenciones

- Código, nombres de variables, comentarios y mensajes de commit en **inglés**.
- Todo el texto visible para el usuario en **español de España**, centralizado en `src/i18n/es.ts`. Ningún literal suelto en los componentes.
- Tipado estricto: sin `any`. Los tipos del frontend se generan desde el OpenAPI del backend.
- Tests donde el coste de un fallo es alto: lógica de la rueda, regla de progresión, deduplicación en la sincronización. No perseguir cobertura en componentes.
- Commits pequeños y atómicos.

---

## Estructura

```
/api                 backend FastAPI
  /app
    /models          SQLAlchemy
    /routers         endpoints
    /services        reglas de negocio (rueda, progresión, sustituciones)
    /cli             creación de usuarios
  /migrations        Alembic
  /seed              catálogo de ejercicios y rutina inicial
/web                 frontend
  /src
    /components      primitivas y componentes de dominio
    /screens         una carpeta por pantalla
    /lib             cliente API, cola de sincronización, Dexie
    /i18n
/docs
/design              export del prototipo
/deploy              Compose, Caddyfile, script de backup
```

---

## Orden de construcción

Las fases 1-4 son la aplicación mínima usable en el gimnasio. No pasar a la 5 hasta que la 4 funcione en el móvil real.

1. Esquema, migraciones, CLI de usuarios
2. Seed del catálogo de ejercicios y de la rutina
3. API: auth, `/sync`, endpoints de lectura
4. **Sistema de diseño + pantalla Hoy + sesión activa + registro de series**
5. Cronómetro de descanso y sustituciones
6. Cinta y peso corporal
7. Historial, volumen semanal, récords
8. Offline: cola en IndexedDB y service worker
9. Compose, Caddy, backups

---

## Sobre la fase 4

Antes de maquetar ninguna pantalla, extraer del prototipo de `/design`:

- Los tokens de color, tipografía, espaciado y radio a `tailwind.config.ts`
- Las primitivas: botón, tarjeta, hoja inferior, campo numérico con `−`/`+`, cronómetro, y el componente de barra cargada con discos de colores

Ningún componente de pantalla define colores ni tamaños propios. Si hace falta un valor que no está en los tokens, se añade al token y se justifica. Es lo que evita que el resultado final se aleje del prototipo pantalla a pantalla.

El componente de barra cargada es el elemento firma del diseño: recibe un peso en kg y dibuja la barra con los discos según el código de color olímpico. Merece su propio test.
