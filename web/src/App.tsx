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
  type ActiveSession,
} from "./lib/session";
import { enqueue, flush, startSync, subscribePending } from "./lib/sync";
import { useRestTimer } from "./lib/useRestTimer";
import { useStopwatch } from "./lib/useStopwatch";
import { Ajustes } from "./screens/Ajustes";
import { Detalle } from "./screens/Detalle";
import { Historial } from "./screens/Historial";
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
  const [tema, setTema] = useState<Tema>("clara");
  const [user, setUser] = useState<UserOut | null | undefined>(undefined);

  useEffect(() => {
    startSync(); // flush the offline queue on load, on reconnect, and periodically
    api.me().then(setUser).catch(() => setUser(null));
  }, []);

  const toggleTema = () => setTema(tema === "clara" ? "oscura" : "clara");

  return (
    <div data-tema={tema} className="flex min-h-full justify-center bg-bg">
      <div className="relative flex h-[100dvh] w-full max-w-[390px] flex-col overflow-hidden bg-bg">
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
  const [tab, setTab] = useState<Tab>("hoy");
  const [ajustes, setAjustes] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);
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

  const toggleTreadmill = () => {
    if (treadmill.running) {
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
        });
      }
    } else {
      treadmill.start();
    }
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

  const end = async () => {
    const active = sessionRef.current;
    if (active) await enqueue({ sessions: [sessionIn(active, "completed")] });
    setActive(null);
    rest.skip();
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

  if (detailId) {
    return <Detalle exerciseId={detailId} onBack={() => setDetailId(null)} />;
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
            subtitle={alts[0]?.pattern}
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
                    <ExerciseThumb name={alt.name} />
                    <div className="min-w-0 flex-1">
                      <div className="text-[15px] font-medium">{alt.name}</div>
                      <div className="mt-1 font-mono text-[11px] text-gris">
                        {alt.substitution_count >= 2
                          ? es.substitutions.oftenSwap
                          : alt.equipment}
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
          {tab === "hoy" ? (
            <Hoy
              today={today}
              positions={positions}
              bodyweight={bodyweight}
              treadmillSeconds={treadmill.seconds}
              treadmillRunning={treadmill.running}
              treadmillKcal={treadmillKcal}
              onTreadmillToggle={toggleTreadmill}
              onLogWeight={openWeightSheet}
              onStart={() => void start()}
              onSkip={() => void skip()}
              onExercise={setDetailId}
              onSettings={() => setAjustes(true)}
            />
          ) : tab === "historial" ? (
            <Historial onSettings={() => setAjustes(true)} />
          ) : (
            <Rutina onSettings={() => setAjustes(true)} />
          )}
        </div>
        <BottomNav active={tab} onSelect={setTab} />
      </div>
      {weightSheetOpen && (
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
      )}
    </>
  );
}
