import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ExerciseThumb } from "../components/ExerciseThumb";
import { WheelIndicator } from "../components/WheelIndicator";
import { es } from "../i18n/es";
import type { BodyWeightSummary, RoutineDayExerciseOut, TodayOut } from "../lib/api";
import { mmss, numEs } from "../lib/format";

interface HoyProps {
  today: TodayOut;
  positions: number;
  bodyweight: BodyWeightSummary | null;
  treadmillSeconds: number;
  treadmillRunning: boolean;
  treadmillKcal: number | null;
  onTreadmillToggle: () => void;
  onLogWeight: () => void;
  onStart: () => void;
  onLogout: () => void;
}

function planLabel(rde: RoutineDayExerciseOut): string {
  const reps = rde.rep_min === rde.rep_max ? `${rde.rep_max}` : `${rde.rep_min}-${rde.rep_max}`;
  return `${rde.target_sets}×${reps}`;
}

export function Hoy({
  today,
  positions,
  bodyweight,
  treadmillSeconds,
  treadmillRunning,
  treadmillKcal,
  onTreadmillToggle,
  onLogWeight,
  onStart,
  onLogout,
}: HoyProps) {
  const { day } = today;
  const totalSets = day.exercises.reduce((acc, e) => acc + e.target_sets, 0);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-4 pb-6 pt-4">
        <div className="flex flex-col gap-4">
          <header className="flex items-center gap-2">
            <span className="font-display text-3xl">hoy</span>
            <div className="ml-auto">
              <WheelIndicator positions={positions} current={today.next_position} />
            </div>
            <Button variant="ghost" onClick={onLogout} className="!min-h-0 !px-3 !py-1.5">
              {es.actions.logout}
            </Button>
          </header>

          <Card className="p-4">
            <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
              {es.today.now}
            </div>
            <div className="mt-2 font-display text-[33px] leading-tight">
              {es.today.session} {today.next_position} · {day.name}
            </div>
            <div className="text-sm text-gris">
              {day.exercises.length} {es.today.exercises} · {totalSets} {es.today.sets}
            </div>

            <div className="mt-4 flex flex-col gap-2.5">
              {day.exercises.map((rde) => (
                <div key={rde.id} className="flex items-center gap-3">
                  <ExerciseThumb name={rde.exercise.name} />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium leading-tight">
                      {rde.exercise.name}
                    </div>
                    <div className="mt-1 font-mono text-[11px] text-gris">
                      {planLabel(rde)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-3">
            <Card className="flex flex-col p-3">
              <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
                {es.today.treadmill}
              </div>
              <div
                className="mt-1.5 font-mono text-[28px] tabular-nums"
                style={{ color: treadmillRunning ? "var(--blue)" : "var(--ink)" }}
              >
                {mmss(treadmillSeconds)}
              </div>
              <div className="mb-2.5 h-4 font-mono text-[11px] text-gris">
                {treadmillKcal !== null && treadmillSeconds > 0
                  ? es.today.kcal(treadmillKcal)
                  : ""}
              </div>
              <button
                type="button"
                onClick={onTreadmillToggle}
                className="mt-auto h-touch rounded-card border border-ink bg-ink text-sm font-medium text-paper"
              >
                {treadmillRunning ? es.today.treadmillStop : es.today.treadmillStart}
              </button>
            </Card>

            <Card
              className="flex cursor-pointer flex-col p-3"
              role="button"
              onClick={onLogWeight}
            >
              <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
                {es.today.bodyweight}
              </div>
              <div className="mt-1.5 font-mono text-[28px] tabular-nums">
                {bodyweight?.avg7 != null ? numEs(bodyweight.avg7) : es.today.noData}
              </div>
              <div className="text-xs text-gris">{es.today.weekAverage}</div>
              {bodyweight?.delta_week != null && (
                <div className="mt-2 font-mono text-xs text-gris">
                  {(bodyweight.delta_week > 0 ? "+" : "") + numEs(bodyweight.delta_week)}{" "}
                  {es.today.vsPrevious}
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>

      <div className="border-t border-line bg-bg px-4 py-3">
        <Button variant="primary" onClick={onStart} className="w-full">
          {es.actions.start}
        </Button>
      </div>
    </div>
  );
}
