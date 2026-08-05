import { useEffect, useState } from "react";

import { BarbellChart } from "../components/BarbellChart";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { es } from "../i18n/es";
import {
  api,
  type BodyWeightSummary,
  type RecordOut,
  type SessionOut,
  type VolumeGroup,
} from "../lib/api";
import { dateShortEs, durationMin, numEs } from "../lib/format";

interface HistorialProps {
  onSettings: () => void;
}

interface Data {
  history: SessionOut[];
  volume: VolumeGroup[];
  records: RecordOut[];
  bodyweight: BodyWeightSummary;
}

const ADHERENCE_DAYS = 28;
const VOLUME_MAX = 20; // useful-range ceiling for bar scaling
const patternLabel = (p: string) => p.replace(/_/g, " ");

/** Last-28-days grid: each day filled if a session was completed that day. */
function adherenceGrid(history: SessionOut[]): { completed: number; days: boolean[] } {
  const done = new Set(
    history
      .filter((s) => s.status === "completed" && s.ended_at)
      .map((s) => (s.ended_at as string).slice(0, 10)),
  );
  const today = new Date();
  const days: boolean[] = [];
  for (let i = ADHERENCE_DAYS - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    days.push(done.has(d.toISOString().slice(0, 10)));
  }
  return { completed: done.size, days };
}

/** 7-day moving average over the raw points, as SVG polyline coordinates. */
function bodyweightLine(points: BodyWeightSummary["points"]): string | null {
  if (points.length < 2) return null;
  const avg = points.map((p) => {
    const end = Date.parse(p.measured_on);
    const window = points.filter(
      (q) => Date.parse(q.measured_on) > end - 7 * 86400000 && Date.parse(q.measured_on) <= end,
    );
    return window.reduce((a, q) => a + q.weight_kg, 0) / window.length;
  });
  const min = Math.min(...avg) - 0.4;
  const max = Math.max(...avg) + 0.4;
  const span = max - min || 1;
  return avg
    .map((v, i) => {
      const x = (i / (avg.length - 1)) * 100;
      const y = 40 - ((v - min) / span) * 38;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function Historial({ onSettings }: HistorialProps) {
  const [data, setData] = useState<Data | null>(null);

  useEffect(() => {
    Promise.all([api.history(), api.volume(), api.records(), api.bodyweight()])
      .then(([history, volume, records, bodyweight]) =>
        setData({ history, volume, records, bodyweight }),
      )
      .catch(() => undefined);
  }, []);

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center font-mono text-xs text-gris">
        {es.history.loading}
      </div>
    );
  }

  const { completed, days } = adherenceGrid(data.history);
  const line = bodyweightLine(data.bodyweight.points);

  return (
    <div className="h-full overflow-y-auto px-4 pb-6 pt-4">
      <header className="mb-4 flex items-center">
        <h1 className="font-display text-3xl">{es.history.title}</h1>
        <Button variant="ghost" onClick={onSettings} className="ml-auto !min-h-0 !px-3 !py-1.5">
          {es.actions.settings}
        </Button>
      </header>

      {data.history.length === 0 ? (
        <Card className="p-5 text-sm text-gris">{es.history.empty}</Card>
      ) : (
        <div className="flex flex-col gap-5">
          {/* Adherencia */}
          <Card className="p-4">
            <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
              {es.history.adherence}
            </div>
            <div className="my-2 font-display text-[42px] leading-none">{completed}</div>
            <div className="mb-3 font-mono text-[11px] text-gris">
              {es.history.sessionsIn4w(completed)}
            </div>
            <div className="grid grid-cols-7 gap-1">
              {days.map((on, i) => (
                <span
                  key={i}
                  className="h-5 rounded-chip border border-line"
                  style={{ background: on ? "var(--green)" : "transparent" }}
                />
              ))}
            </div>
          </Card>

          {/* Volumen semanal */}
          {data.volume.length > 0 && (
            <Card className="p-4">
              <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
                {es.history.volume}
              </div>
              <div className="mb-3 font-mono text-[10px] text-gris">
                {es.history.volumeHint}
              </div>
              <div className="flex flex-col gap-2">
                {data.volume.map((g) => (
                  <div key={g.pattern} className="flex items-center gap-2">
                    <span className="w-32 shrink-0 text-[13px]">{patternLabel(g.pattern)}</span>
                    <div className="h-2.5 flex-1 rounded-full bg-line">
                      <div
                        className="h-full rounded-full bg-blue"
                        style={{ width: `${Math.min(g.sets / VOLUME_MAX, 1) * 100}%` }}
                      />
                    </div>
                    <span className="w-6 text-right font-mono text-xs tabular-nums">
                      {g.sets}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Récords */}
          {data.records.length > 0 && (
            <Card className="p-4">
              <div className="mb-3 font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
                {es.history.records}
              </div>
              <div className="flex flex-col">
                {data.records.map((r) => (
                  <div
                    key={r.exercise_id}
                    className="flex items-center gap-3 border-t border-line py-2.5 first:border-t-0"
                  >
                    <BarbellChart weightKg={r.weight_kg} compact />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm">{r.exercise_name}</div>
                      <div className="font-mono text-[11px] text-gris">
                        {numEs(r.weight_kg)}×{r.reps}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-sm tabular-nums text-red">
                        {numEs(r.one_rm)}
                      </span>
                      <span className="font-mono text-[10px] text-gris"> 1rm</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Peso corporal */}
          {line && (
            <Card className="p-4">
              <div className="mb-3 font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
                {es.history.bodyweight}
              </div>
              <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="h-16 w-full">
                <polyline
                  points={line}
                  fill="none"
                  stroke="var(--blue)"
                  strokeWidth={1.4}
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
            </Card>
          )}

          {/* Sesiones */}
          <div>
            <div className="mb-1 font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
              {es.history.sessions}
            </div>
            {data.history.map((s) => (
              <div
                key={s.id}
                className="flex items-center gap-3 border-b border-line py-3"
              >
                <span className="w-12 font-mono text-[11px] text-gris">
                  {dateShortEs(s.started_at)}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium">
                    {es.history.session} {s.position} · {s.day_name}
                  </div>
                  <div className="mt-0.5 font-mono text-[11px] text-gris">
                    {s.set_count} {es.today.sets}
                    {s.ended_at
                      ? ` · ${es.history.minutes(durationMin(s.started_at, s.ended_at))}`
                      : ""}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
