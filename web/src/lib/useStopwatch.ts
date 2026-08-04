import { useCallback, useEffect, useState } from "react";

export interface StopwatchResult {
  startedAt: string; // ISO
  endedAt: string; // ISO
  durationS: number;
}

export interface Stopwatch {
  seconds: number;
  running: boolean;
  start: () => void;
  stop: () => StopwatchResult | null;
}

/**
 * Count-up timer driven by an absolute start timestamp (spec regla 5): elapsed
 * is recomputed against Date.now() each tick and on foreground, so it stays
 * correct across a backgrounded PWA. Used for the treadmill.
 */
export function useStopwatch(): Stopwatch {
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (startedAt === null) return;
    const tick = () => setSeconds(Math.floor((Date.now() - startedAt) / 1000));
    tick();
    const id = window.setInterval(tick, 250);
    const onVisible = () => {
      if (document.visibilityState === "visible") tick();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(id);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [startedAt]);

  const start = useCallback(() => {
    setStartedAt(Date.now());
    setSeconds(0);
  }, []);

  const stop = useCallback((): StopwatchResult | null => {
    if (startedAt === null) return null;
    const end = Date.now();
    const result: StopwatchResult = {
      startedAt: new Date(startedAt).toISOString(),
      endedAt: new Date(end).toISOString(),
      durationS: Math.floor((end - startedAt) / 1000),
    };
    setStartedAt(null);
    setSeconds(0);
    return result;
  }, [startedAt]);

  return { seconds, running: startedAt !== null, start, stop };
}
