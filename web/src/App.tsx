import { useCallback, useEffect, useRef, useState } from "react";

import { BottomSheet } from "./components/BottomSheet";
import { ExerciseThumb } from "./components/ExerciseThumb";
import { RestBar } from "./components/RestBar";
import { es } from "./i18n/es";
import {
  ApiError,
  api,
  type AlternativeOut,
  type TodayOut,
  type UserOut,
} from "./lib/api";
import {
  buildSession,
  sessionIn,
  setLogIn,
  swapExercise,
  type ActiveSession,
} from "./lib/session";
import { pushEvents, resetCursor } from "./lib/sync";
import { useRestTimer } from "./lib/useRestTimer";
import { Hoy } from "./screens/Hoy";
import { Login } from "./screens/Login";
import { Sesion } from "./screens/Sesion";

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
    api.me().then(setUser).catch(() => setUser(null));
  }, []);

  return (
    <div data-tema={tema} className="flex min-h-full justify-center bg-bg">
      <div className="relative flex h-[100dvh] w-full max-w-[390px] flex-col overflow-hidden bg-bg">
        <button
          type="button"
          onClick={() => setTema(tema === "clara" ? "oscura" : "clara")}
          className="absolute right-2 top-2 z-10 rounded-chip border border-line bg-paper/70 px-2 py-1 font-mono text-[9px] text-gris"
        >
          {tema === "clara" ? "oscura" : "clara"}
        </button>
        {user === undefined ? (
          <div className="flex h-full items-center justify-center font-mono text-xs text-gris">
            …
          </div>
        ) : user ? (
          <Shell onLogout={() => setUser(null)} />
        ) : (
          <Login onLogin={setUser} />
        )}
      </div>
    </div>
  );
}

interface ShellProps {
  onLogout: () => void;
}

function Shell({ onLogout }: ShellProps) {
  const [today, setToday] = useState<TodayOut | null>(null);
  const [positions, setPositions] = useState(5);
  const [session, setSession] = useState<ActiveSession | null>(null);
  const [offline, setOffline] = useState(false);
  const [sheetExIdx, setSheetExIdx] = useState<number | null>(null);
  const [alts, setAlts] = useState<AlternativeOut[]>([]);
  const sessionRef = useRef<ActiveSession | null>(null);
  const rest = useRestTimer();

  const setActive = (next: ActiveSession | null) => {
    sessionRef.current = next;
    setSession(next);
  };

  const load = useCallback(async () => {
    const [t, routine] = await Promise.all([api.today(), api.routine()]);
    setToday(t);
    setPositions(routine.days.length);
  }, []);

  useEffect(() => {
    load().catch((err) => {
      if (err instanceof ApiError && err.status === 401) onLogout();
    });
  }, [load, onLogout]);

  const safePush = useCallback(
    async (events: Parameters<typeof pushEvents>[0]) => {
      try {
        await pushEvents(events);
        setOffline(false);
      } catch {
        setOffline(true); // phase 8: enqueue in IndexedDB and retry on reconnect
      }
    },
    [],
  );

  const start = () => {
    if (!today) return;
    const active = buildSession(today.day);
    setActive(active);
    void safePush({ sessions: [sessionIn(active, "in_progress")] });
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
      void safePush({ set_logs: [setLogIn(next, nextEx, nextEx.sets[setIdx]!)] });
    } else {
      // Append-only: void the logged set and give the row a fresh id so a later
      // re-check inserts a new set rather than trying to un-void (spec regla 1).
      void safePush({ set_logs: [{ ...setLogIn(current, ex, set), voided: true }] });
      setActive(patchSet(current, exIdx, setIdx, { done: false, id: crypto.randomUUID() }));
    }
  };

  const openSheet = (exIdx: number) => {
    const ex = sessionRef.current?.exercises[exIdx];
    if (!ex) return;
    setSheetExIdx(exIdx);
    setAlts([]);
    api.alternatives(ex.exerciseId).then(setAlts).catch(() => setAlts([]));
  };

  const closeSheet = () => {
    setSheetExIdx(null);
    setAlts([]);
  };

  const pick = (alt: AlternativeOut) => {
    if (sessionRef.current && sheetExIdx !== null) {
      setActive(swapExercise(sessionRef.current, sheetExIdx, alt));
    }
    closeSheet();
  };

  const end = async () => {
    const active = sessionRef.current;
    if (active) await safePush({ sessions: [sessionIn(active, "completed")] });
    setActive(null);
    rest.skip();
    resetCursor();
    await load().catch(() => undefined);
  };

  if (!today) {
    return (
      <div className="flex h-full items-center justify-center font-mono text-xs text-gris">
        …
      </div>
    );
  }

  if (session) {
    return (
      <>
        <Sesion
          session={session}
          positionLabel={`${es.today.session} ${today.next_position} · ${today.day.name}`}
          offline={offline}
          onWeight={onWeight}
          onReps={onReps}
          onCheck={onCheck}
          onBusy={openSheet}
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

  return (
    <Hoy today={today} positions={positions} onStart={start} onLogout={onLogout} />
  );
}
