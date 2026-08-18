import { useCallback, useEffect, useState } from "react";

export interface StopwatchResult {
  startedAt: string; // ISO
  endedAt: string; // ISO
  durationS: number;
}

export interface Stopwatch {
  seconds: number;
  running: boolean;
  /** Started but currently paused: the run exists, the clock does not advance. */
  paused: boolean;
  start: () => void;
  pause: () => void;
  resume: () => void;
  stop: () => StopwatchResult | null;
}

/**
 * Count-up timer driven by absolute timestamps (spec regla 5): elapsed is
 * recomputed against Date.now() on every tick and on foreground, so it survives
 * a backgrounded PWA.
 *
 * Pausing banks the seconds run so far and drops the running mark, so time spent
 * stopped — a drink, waiting for a machine — never reaches the saved duration.
 */
export function useStopwatch(): Stopwatch {
  // When the current segment began; null while paused or stopped.
  const [runningSince, setRunningSince] = useState<number | null>(null);
  // Seconds banked by earlier segments of this same run.
  const [banked, setBanked] = useState(0);
  // First start of the run, kept as the saved record's startedAt.
  const [firstStartedAt, setFirstStartedAt] = useState<number | null>(null);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (runningSince === null) return;
    const tick = () =>
      setSeconds(banked + Math.floor((Date.now() - runningSince) / 1000));
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
  }, [runningSince, banked]);

  const start = useCallback(() => {
    const now = Date.now();
    setFirstStartedAt(now);
    setRunningSince(now);
    setBanked(0);
    setSeconds(0);
  }, []);

  const pause = useCallback(() => {
    if (runningSince === null) return;
    const total = banked + Math.floor((Date.now() - runningSince) / 1000);
    setBanked(total);
    setSeconds(total);
    setRunningSince(null);
  }, [banked, runningSince]);

  const resume = useCallback(() => {
    if (firstStartedAt === null || runningSince !== null) return;
    setRunningSince(Date.now());
  }, [firstStartedAt, runningSince]);

  const stop = useCallback((): StopwatchResult | null => {
    if (firstStartedAt === null) return null;
    const end = Date.now();
    const elapsed =
      runningSince === null
        ? banked
        : banked + Math.floor((end - runningSince) / 1000);
    setRunningSince(null);
    setFirstStartedAt(null);
    setBanked(0);
    setSeconds(0);
    // Nothing worth storing if it was stopped before a second elapsed.
    if (elapsed <= 0) return null;
    return {
      startedAt: new Date(firstStartedAt).toISOString(),
      endedAt: new Date(end).toISOString(),
      durationS: elapsed,
    };
  }, [banked, firstStartedAt, runningSince]);

  return {
    seconds,
    running: runningSince !== null,
    paused: runningSince === null && firstStartedAt !== null,
    start,
    pause,
    resume,
    stop,
  };
}
