import { useCallback, useEffect, useRef, useState } from "react";

import { BottomNav, type Tab } from "./components/BottomNav";
import { BottomSheet } from "./components/BottomSheet";
import { Button } from "./components/Button";
import { ExerciseThumb } from "./components/ExerciseThumb";
import { NumberStepper } from "./components/NumberStepper";
import { RestBar } from "./components/RestBar";
import { es } from "./i18n/es";
import {
  ApiError,
  api,
  type AlternativeOut,
  type BodyWeightSummary,
  type TodayOut,
  type UserOut,
} from "./lib/api";
import {
  buildSession,
  sessionIn,
  setLogIn,
  substitute,
  summarize,
  type ActiveSession,
  type SessionSummary,
} from "./lib/session";
import { equipmentLabel, patternLabel } from "./lib/labels";
import { enqueue, flush, startSync, subscribePending } from "./lib/sync";
import { useBackButton } from "./lib/useBackButton";
import { useRestTimer } from "./lib/useRestTimer";
import { useStopwatch } from "./lib/useStopwatch";
import { Ajustes } from "./screens/Ajustes";
import { Cinta } from "./screens/Cinta";
import { Detalle } from "./screens/Detalle";
import { Fases } from "./screens/Fases";
import { Inicio } from "./screens/Inicio";
import { Laboratorio } from "./screens/Laboratorio";
import { Peso } from "./screens/Peso";
import { Highlights } from "./screens/Highlights";
import { Historial } from "./screens/Historial";
import { Asistente } from "./screens/Asistente";
import { Rutina } from "./screens/Rutina";
import { Hoy } from "./screens/Hoy";
import { Login } from "./screens/Login";
import { Sesion } from "./screens/Sesion";

function todayISODate(): string {
  return new Date().toISOString().slice(0, 10);
}

type Tema = "clara" | "oscura";

function patchSet(
  session: ActiveSession,
  exIdx: number,
  setIdx: number,
  patch: Partial<ActiveSession["exercises"][number]["sets"][number]>,
): ActiveSession {
  return {
    ...session,
    exercises: session.exercises.map((ex, i) =>
      i !== exIdx
        ? ex
        : { ...ex, sets: ex.sets.map((s, j) => (j !== setIdx ? s : { ...s, ...patch })) },
    ),
  };
}

/** Auth gate + phone frame. */
export function App() {
  const [tema, setTema] = useState<Tema>(() =>
    localStorage.getItem("tema") === "oscura" ? "oscura" : "clara",
  );
  const [user, setUser] = useState<UserOut | null | undefined>(undefined);

  useEffect(() => {
    startSync(); // flush the offline queue on load, on reconnect, and periodically
    api.me().then(setUser).catch(() => setUser(null));
  }, []);

  // The theme lives on <html>: anything inheriting from body (text with no
  // explicit colour class) must resolve --ink from the themed scope, otherwise
  // it keeps the light value and renders black on the dark background.
  useEffect(() => {
    document.documentElement.setAttribute("data-tema", tema);
    localStorage.setItem("tema", tema);
    // The installed app paints its own chrome from this: left fixed it would
    // show a light bar around a dark screen.
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", tema === "oscura" ? "#16181a" : "#E9E7E2");
  }, [tema]);

  const toggleTema = () => setTema(tema === "clara" ? "oscura" : "clara");

  return (
    <div className="flex min-h-full justify-center bg-bg">
      <div
        className="relative flex h-[100dvh] w-full max-w-[390px] flex-col overflow-hidden bg-bg"
        style={{ paddingLeft: "var(--safe-left)", paddingRight: "var(--safe-right)" }}
      >
        {user === undefined ? (
          <div className="flex h-full items-center justify-center font-mono text-xs text-gris">
            …
          </div>
        ) : user ? (
          <Shell
            user={user}
            tema={tema}
            onToggleTema={toggleTema}
            onLogout={() => setUser(null)}
          />
        ) : (
          <Login onLogin={setUser} />
        )}
      </div>
    </div>
  );
}

interface ShellProps {
  user: UserOut;
  tema: Tema;
  onToggleTema: () => void;
  onLogout: () => void;
}

function Shell({ user, tema, onToggleTema, onLogout }: ShellProps) {
  const [today, setToday] = useState<TodayOut | null>(null);
  const [positions, setPositions] = useState(5);
  const [session, setSession] = useState<ActiveSession | null>(null);
  const [pending, setPending] = useState(0);
  const [sheetExIdx, setSheetExIdx] = useState<number | null>(null);
  const [alts, setAlts] = useState<AlternativeOut[]>([]);
  const [bodyweight, setBodyweight] = useState<BodyWeightSummary | null>(null);
  const [weightSheetOpen, setWeightSheetOpen] = useState(false);
  const [weightInput, setWeightInput] = useState(70);
  const [tab, setTab] = useState<Tab>("inicio");
  const [ajustes, setAjustes] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);
  // Full-screen views reached from a tab (treadmill and body weight detail).
  const [subScreen, setSubScreen] = useState<"cinta" | "peso" | "fases" | "asistente" | "lab" | null>(null);
  const [highlights, setHighlights] = useState<SessionSummary | null>(null);
  const sessionRef = useRef<ActiveSession | null>(null);
  const rest = useRestTimer();
  const treadmill = useStopwatch();

  const setActive = (next: ActiveSession | null) => {
    sessionRef.current = next;
    setSession(next);
  };

  const load = useCallback(async () => {
    const [t, routine, bw] = await Promise.all([
      api.today(),
      api.routine(),
      api.bodyweight(),
    ]);
    setToday(t);
    setPositions(routine.days.length);
    setBodyweight(bw);
  }, []);

  useEffect(() => {
    load().catch((err) => {
      if (err instanceof ApiError && err.status === 401) onLogout();
    });
  }, [load, onLogout]);

  useEffect(() => subscribePending(setPending), []);

  // The phone's back button, innermost first. An active session deliberately
  // swallows the press: losing a workout to a stray thumb would be the worst
  // bug in the app.
  useBackButton([
    { open: sheetExIdx !== null, close: () => setSheetExIdx(null) },
    { open: weightSheetOpen, close: () => setWeightSheetOpen(false) },
    { open: highlights !== null, close: () => setHighlights(null) },
    { open: detailId !== null, close: () => setDetailId(null) },
    { open: ajustes, close: () => setAjustes(false) },
    { open: subScreen !== null, close: () => setSubScreen(null) },
    { open: session !== null, close: () => undefined },
    { open: tab !== "inicio", close: () => setTab("inicio") },
  ]);

  const start = async () => {
    if (!today) return;
    const suggestions = await api.suggestions(today.day.id).catch(() => []);
    const active = buildSession(today.day, suggestions);
    setActive(active);
    void enqueue({ sessions: [sessionIn(active, "in_progress")] });
  };

  const skip = async () => {
    await api.skip().catch(() => undefined);
    await load().catch(() => undefined);
  };

  const onNotes = (value: string) => {
    if (!sessionRef.current) return;
    setActive({ ...sessionRef.current, notes: value });
  };

  const onWeight = (exIdx: number, setIdx: number, next: number) => {
    if (!sessionRef.current) return;
    setActive(patchSet(sessionRef.current, exIdx, setIdx, { weightKg: next }));
  };

  const onReps = (exIdx: number, setIdx: number, next: number) => {
    if (!sessionRef.current) return;
    setActive(patchSet(sessionRef.current, exIdx, setIdx, { reps: next }));
  };

  const onCheck = (exIdx: number, setIdx: number) => {
    const current = sessionRef.current;
    if (!current) return;
    const ex = current.exercises[exIdx];
    const set = ex?.sets[setIdx];
    if (!ex || !set) return;

    if (!set.done) {
      const next = patchSet(current, exIdx, setIdx, { done: true });
      const nextEx = next.exercises[exIdx]!;
      setActive(next);
      rest.start(nextEx.restS); // absolute-timestamp rest countdown (regla 5)
      void enqueue({ set_logs: [setLogIn(next, nextEx, nextEx.sets[setIdx]!)] });
    } else {
      // Append-only: void the logged set and give the row a fresh id so a later
      // re-check inserts a new set rather than trying to un-void (spec regla 1).
      void enqueue({ set_logs: [{ ...setLogIn(current, ex, set), voided: true }] });
      setActive(patchSet(current, exIdx, setIdx, { done: false, id: crypto.randomUUID() }));
    }
  };

  const openSheet = (exIdx: number) => {
    const ex = sessionRef.current?.exercises[exIdx];
    if (!ex) return;
    setSheetExIdx(exIdx);
    setAlts([]);
    api.alternatives(ex.plannedExerciseId).then(setAlts).catch(() => setAlts([]));
  };

  const closeSheet = () => {
    setSheetExIdx(null);
    setAlts([]);
  };

  const pick = (alt: AlternativeOut) => {
    if (sessionRef.current && sheetExIdx !== null) {
      setActive(substitute(sessionRef.current, sheetExIdx, alt));
    }
    closeSheet();
  };

  /** Stop the run and queue it. Shared by the Hoy card and the Cinta screen so
   * a run started in one place can be finished in the other. */
  const saveTreadmill = () => {
    const result = treadmill.stop();
    if (result && result.durationS > 0) {
      void enqueue({
        treadmill_sessions: [
          {
            id: crypto.randomUUID(),
            started_at: result.startedAt,
            ended_at: result.endedAt,
            duration_s: result.durationS,
          },
        ],
      }).then(() => flush());
    }
  };

  const toggleTreadmill = () => {
    if (treadmill.running || treadmill.paused) saveTreadmill();
    else treadmill.start();
  };

  const openWeightSheet = () => {
    setWeightInput(bodyweight?.latest ?? 70);
    setWeightSheetOpen(true);
  };

  const saveWeight = async () => {
    setWeightSheetOpen(false);
    await enqueue({
      body_weights: [
        {
          id: crypto.randomUUID(),
          measured_on: todayISODate(),
          weight_kg: weightInput,
        },
      ],
    });
    await flush();
    setBodyweight(await api.bodyweight().catch(() => bodyweight));
  };

  const treadmillKcal =
    bodyweight?.latest != null
      ? Math.round((treadmill.seconds / 60) * 0.053 * bodyweight.latest)
      : null;

  // One sheet, reachable from the Hoy card and from the body-weight screen.
  const weightSheet = (
    <BottomSheet title={es.today.bodyweight} onClose={() => setWeightSheetOpen(false)}>
      <div className="flex items-center justify-between gap-3 py-2">
        <NumberStepper
          label={es.today.bodyweight}
          value={weightInput}
          step={0.1}
          onChange={setWeightInput}
          valueWidth={72}
        />
        <Button variant="primary" onClick={() => void saveWeight()} className="flex-1">
          {es.today.save}
        </Button>
      </div>
    </BottomSheet>
  );

  const end = async () => {
    const active = sessionRef.current;
    if (!active) return;
    const summary: SessionSummary = {
      positionLabel: today
        ? `${es.today.session} ${today.next_position} · ${today.day.name}`
        : "",
      ...summarize(active, bodyweight?.latest ?? null),
    };
    await enqueue({ sessions: [sessionIn(active, "completed")] });
    setActive(null);
    rest.skip();
    setHighlights(summary);
    await flush(); // ensure the completion reaches the server before reloading
    await load().catch(() => undefined);
  };

  if (!today) {
    return (
      <div className="flex h-full items-center justify-center font-mono text-xs text-gris">
        …
      </div>
    );
  }

  if (highlights) {
    return <Highlights summary={highlights} onDone={() => setHighlights(null)} />;
  }

  if (detailId) {
    return <Detalle exerciseId={detailId} onBack={() => setDetailId(null)} />;
  }

  if (subScreen === "fases") {
    return <Fases onBack={() => setSubScreen(null)} />;
  }

  if (subScreen === "lab") {
    return <Laboratorio onBack={() => setSubScreen(null)} />;
  }

  if (subScreen === "asistente") {
    return (
      <Asistente
        onBack={() => setSubScreen(null)}
        onChanged={() => void load()}
      />
    );
  }

  if (subScreen === "cinta") {
    return (
      <Cinta
        watch={treadmill}
        onSave={saveTreadmill}
        onBack={() => setSubScreen(null)}
      />
    );
  }

  if (subScreen === "peso") {
    return (
      <>
        <Peso
          data={bodyweight}
          onLog={openWeightSheet}
          onBack={() => setSubScreen(null)}
        />
        {weightSheetOpen && weightSheet}
      </>
    );
  }

  if (session) {
    return (
      <>
        <Sesion
          session={session}
          positionLabel={`${es.today.session} ${today.next_position} · ${today.day.name}`}
          offline={pending > 0}
          onWeight={onWeight}
          onReps={onReps}
          onCheck={onCheck}
          onBusy={openSheet}
          onExercise={setDetailId}
          onNotes={onNotes}
          onEnd={() => void end()}
        />
        {rest.running && (
          <RestBar seconds={rest.seconds} onAdd={() => rest.add(15)} onSkip={rest.skip} />
        )}
        {sheetExIdx !== null && (
          <BottomSheet
            title={es.substitutions.title}
            subtitle={alts[0] ? patternLabel(alts[0].pattern) : undefined}
            onClose={closeSheet}
          >
            {alts.length === 0 ? (
              <p className="py-4 text-sm text-gris">{es.substitutions.empty}</p>
            ) : (
              <div className="flex flex-col gap-2">
                {alts.map((alt) => (
                  <button
                    key={alt.id}
                    type="button"
                    onClick={() => pick(alt)}
                    className="flex items-center gap-3 rounded-card border border-line bg-paper p-2.5 text-left"
                  >
                    <ExerciseThumb name={alt.name} exerciseId={alt.id} />
                    <div className="min-w-0 flex-1">
                      <div className="text-[15px] font-medium">{alt.name}</div>
                      <div className="mt-1 font-mono text-[11px] text-gris">
                        {alt.substitution_count >= 2
                          ? es.substitutions.oftenSwap
                          : equipmentLabel(alt.equipment)}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </BottomSheet>
        )}
      </>
    );
  }

  if (ajustes) {
    return (
      <Ajustes
        user={user}
        onPhases={() => {
          setAjustes(false);
          setSubScreen("fases");
        }}
        tema={tema}
        onToggleTema={onToggleTema}
        onBack={() => setAjustes(false)}
        onLogout={onLogout}
      />
    );
  }

  return (
    <>
      <div className="flex h-full flex-col">
        <div className="min-h-0 flex-1">
          {tab === "inicio" ? (
            <Inicio
              onStart={() => {
                setTab("hoy");
                void start();
              }}
              onTreadmill={() => setSubScreen("cinta")}
              onWeight={() => setSubScreen("peso")}
            onLab={() => setSubScreen("lab")}
              onSettings={() => setAjustes(true)}
            />
          ) : tab === "hoy" ? (
            <Hoy
              today={today}
              positions={positions}
              bodyweight={bodyweight}
              treadmillSeconds={treadmill.seconds}
              treadmillRunning={treadmill.running}
              treadmillPaused={treadmill.paused}
              treadmillKcal={treadmillKcal}
              onTreadmillToggle={toggleTreadmill}
              onTreadmillPause={treadmill.paused ? treadmill.resume : treadmill.pause}
              onTreadmillOpen={() => setSubScreen("cinta")}
              onLogWeight={openWeightSheet}
              onWeightOpen={() => setSubScreen("peso")}
              onStart={() => void start()}
              onSkip={() => void skip()}
              onExercise={setDetailId}
            />
          ) : tab === "historial" ? (
            <Historial />
          ) : (
            <Rutina onAssistant={() => setSubScreen("asistente")} />
          )}
        </div>
        <BottomNav active={tab} onSelect={setTab} />
      </div>
      {weightSheetOpen && weightSheet}
    </>
  );
}
