import { useCallback, useEffect, useState } from "react";

/**
 * Rest countdown driven by an ABSOLUTE end timestamp (spec §5.4, regla 5), never
 * by accumulating setInterval ticks. Remaining time is recomputed against
 * Date.now() on every tick and whenever the tab returns to the foreground, so a
 * backgrounded PWA (iOS especially) still shows the right number on resume.
 */
export interface RestTimer {
  seconds: number;
  running: boolean;
  start: (seconds: number) => void;
  add: (seconds: number) => void;
  skip: () => void;
}

export function useRestTimer(): RestTimer {
  const [endsAt, setEndsAt] = useState<number | null>(null);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (endsAt === null) return;

    const tick = () => {
      const left = Math.max(0, Math.round((endsAt - Date.now()) / 1000));
      setSeconds(left);
      if (left <= 0) {
        setEndsAt(null);
        if (navigator.vibrate) navigator.vibrate(180);
      }
    };

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
  }, [endsAt]);

  const start = useCallback((s: number) => setEndsAt(Date.now() + s * 1000), []);
  const add = useCallback(
    (s: number) => setEndsAt((prev) => (prev ?? Date.now()) + s * 1000),
    [],
  );
  const skip = useCallback(() => {
    setEndsAt(null);
    setSeconds(0);
  }, []);

  return { seconds, running: endsAt !== null, start, add, skip };
}
