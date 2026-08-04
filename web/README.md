# gym-web

PWA frontend (React 18 + Vite + TypeScript + Tailwind). Design tokens and the
signature loaded-barbell component are derived from the prototype in `/design`.

## Develop

```bash
cd web
npm install
npm run dev        # http://localhost:5173 (proxies /api -> http://127.0.0.1:8000)
```

## Checks

```bash
npm run test       # vitest — barbell plate maths
npm run typecheck  # tsc --noEmit (strict)
npm run build      # type-check + production build
```

## Design system

- **Tokens** live in `tailwind.config.ts` + `src/index.css` (CSS variables,
  light default, dark via `data-tema="oscura"`). No component defines its own
  colours or sizes — add a token instead.
- **Fonts**: Instrument Serif (display), Inter (body), IBM Plex Mono (data),
  matching the prototype.
- **Primitives**: `Button`, `Card`, `NumberStepper` (44px targets), and
  `BarbellChart` — the signature element; its plate maths (`src/lib/barbell.ts`)
  is unit-tested.

`App.tsx` is a temporary design-system preview; the real screens (Hoy, Sesión
activa) replace it next.
