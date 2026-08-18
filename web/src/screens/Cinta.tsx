import { useEffect, useState } from "react";

import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Header } from "../components/Header";
import { es } from "../i18n/es";
import { api, type TreadmillSummary } from "../lib/api";
import { dateShortEs, mmss } from "../lib/format";
import type { Stopwatch } from "../lib/useStopwatch";

interface CintaProps {
  watch: Stopwatch;
  /** Persists the finished run through the offline queue. */
  onSave: () => void;
  onBack: () => void;
}

const minutes = (seconds: number) => Math.round(seconds / 60);

export function Cinta({ watch, onSave, onBack }: CintaProps) {
  const [data, setData] = useState<TreadmillSummary | null>(null);

  const reload = () => api.treadmill().then(setData).catch(() => undefined);
  useEffect(() => {
    void reload();
  }, []);

  const finish = () => {
    onSave();
    // The run syncs in the background; refresh once it has had a chance to land.
    window.setTimeout(() => void reload(), 600);
  };

  return (
    <div className="h-full overflow-y-auto pb-6"
      style={{ paddingBottom: "calc(1.5rem + var(--safe-bottom))" }}
    >
      <Header
        title={es.treadmillScreen.title}
        leading={
          <Button variant="ghost" onClick={onBack} className="mb-1 !min-h-0 !px-3 !py-1.5">
            {es.actions.back}
          </Button>
        }
      />

      <div className="flex flex-col gap-4 px-4 pt-4">
        <Card className="p-4">
          <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
            {watch.running
              ? es.treadmillScreen.running
              : watch.paused
                ? es.treadmillScreen.paused
                : es.treadmillScreen.title}
          </div>
          <div
            className="mt-1 font-mono text-[56px] leading-none tabular-nums"
            style={{
              color: watch.running
                ? "var(--blue)"
                : watch.paused
                  ? "var(--yellow)"
                  : "var(--ink)",
            }}
          >
            {mmss(watch.seconds)}
          </div>

          <div className="mt-4 flex gap-2">
            {!watch.running && !watch.paused && (
              <Button variant="primary" onClick={watch.start} className="flex-1">
                {es.treadmillScreen.start}
              </Button>
            )}
            {watch.running && (
              <button
                type="button"
                onClick={watch.pause}
                className="h-touch flex-1 rounded-card border border-line text-sm font-medium"
              >
                {es.treadmillScreen.pause}
              </button>
            )}
            {watch.paused && (
              <Button variant="primary" onClick={watch.resume} className="flex-1">
                {es.treadmillScreen.resume}
              </Button>
            )}
            {(watch.running || watch.paused) && (
              <button
                type="button"
                onClick={finish}
                className="h-touch flex-1 rounded-card border border-ink bg-ink text-sm font-medium text-paper"
              >
                {es.treadmillScreen.stop}
              </button>
            )}
          </div>
          {watch.paused && (
            <p className="mt-2 font-mono text-[10px] text-gris">
              {es.treadmillScreen.pausedNote}
            </p>
          )}
        </Card>

        {data && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <Card className="p-3">
                <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
                  {es.treadmillScreen.weekTotal}
                </div>
                <div className="mt-1 font-display text-[30px] leading-none">
                  {minutes(data.week_seconds)}
                  <span className="ml-1 font-mono text-[11px] text-gris">min</span>
                </div>
                {data.week_kcal !== null && (
                  <div className="mt-1 font-mono text-[10px] text-gris">
                    {data.week_kcal} kcal
                  </div>
                )}
              </Card>
              <Card className="p-3">
                <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
                  {es.treadmillScreen.allTime}
                </div>
                <div className="mt-1 font-display text-[30px] leading-none">
                  {minutes(data.total_seconds)}
                  <span className="ml-1 font-mono text-[11px] text-gris">min</span>
                </div>
              </Card>
            </div>

            <Card className="p-4">
              <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
                {es.treadmillScreen.history}
              </div>
              {data.entries.length === 0 ? (
                <p className="mt-2 text-sm text-gris">{es.treadmillScreen.empty}</p>
              ) : (
                <div className="mt-1 flex flex-col">
                  {data.entries.map((e) => (
                    <div
                      key={e.id}
                      className="flex items-center gap-3 border-t border-line py-2.5 first:border-t-0"
                    >
                      <span className="w-12 font-mono text-[11px] text-gris">
                        {dateShortEs(e.started_at)}
                      </span>
                      <span className="flex-1 font-mono text-sm tabular-nums">
                        {mmss(e.duration_s)}
                      </span>
                      <span className="font-mono text-[11px] text-gris">
                        {e.kcal !== null ? `${e.kcal} kcal` : ""}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {data.entries.some((e) => e.kcal === null) && (
                <p className="mt-2 text-[12px] leading-snug text-gris">
                  {es.treadmillScreen.kcalHint}
                </p>
              )}
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
