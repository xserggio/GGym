import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ExerciseThumb } from "../components/ExerciseThumb";
import { Header } from "../components/Header";
import { WheelStrip } from "../components/WheelStrip";
import { es } from "../i18n/es";
import type { BodyWeightSummary, RoutineDayExerciseOut, TodayOut } from "../lib/api";
import { mmss, numEs } from "../lib/format";
import { sessionColor } from "../lib/palette";

interface HoyProps {
  today: TodayOut;
  positions: number;
  bodyweight: BodyWeightSummary | null;
  treadmillSeconds: number;
  treadmillRunning: boolean;
  treadmillPaused: boolean;
  treadmillKcal: number | null;
  onTreadmillToggle: () => void;
  onTreadmillPause: () => void;
  onTreadmillOpen: () => void;
  onLogWeight: () => void;
  onWeightOpen: () => void;
  onStart: () => void;
  onSkip: () => void;
  onExercise: (exerciseId: string) => void;
}

function planLabel(rde: RoutineDayExerciseOut): string {
  const reps = rde.rep_min === rde.rep_max ? `${rde.rep_max}` : `${rde.rep_min}-${rde.rep_max}`;
  const unit = rde.unit === "seconds" ? " s" : "";
  const perSide = rde.exercise.per_side ? ` · ${es.today.perSide}` : "";
  return `${rde.target_sets}×${reps}${unit}${perSide}`;
}

export function Hoy({
  today,
  positions,
  bodyweight,
  treadmillSeconds,
  treadmillRunning,
  treadmillPaused,
  treadmillKcal,
  onTreadmillToggle,
  onTreadmillPause,
  onTreadmillOpen,
  onLogWeight,
  onWeightOpen,
  onStart,
  onSkip,
  onExercise,
}: HoyProps) {
  const { day } = today;
  const totalSets = day.exercises.reduce((acc, e) => acc + e.target_sets, 0);
  const accent = sessionColor(today.next_position);

  return (
    <div className="flex h-full flex-col">
      <Header title={es.nav.today} />
      <WheelStrip positions={positions} current={today.next_position} />
      <div className="flex-1 overflow-y-auto px-4 pb-6 pt-4">
        <div className="flex flex-col gap-4">

          {today.recovery_warning && (
            <div
              className="rounded-card px-3 py-2.5 text-[13px] leading-snug text-ink"
              style={{ background: "rgba(210,51,60,0.08)", borderLeft: "2px solid var(--red)" }}
            >
              {es.today.recovery}
            </div>
          )}
          {today.resume_after_break && (
            <div
              className="rounded-card px-3 py-2.5 text-[13px] leading-snug text-ink"
              style={{ background: "rgba(43,95,217,0.08)", borderLeft: "2px solid var(--blue)" }}
            >
              {es.today.resume}
            </div>
          )}

          <Card className="p-4">
            <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
              {es.today.now}
            </div>
            <div className="mt-2 flex items-center gap-2.5">
              <span
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-chip font-mono text-base"
                style={{ background: accent, color: "var(--paper)" }}
              >
                {today.next_position}
              </span>
              <div className="min-w-0">
                <div className="truncate font-display text-[28px] leading-tight">
                  {day.name}
                </div>
                <div className="text-sm text-gris">
                  {day.exercises.length} {es.today.exercises} · {totalSets} {es.today.sets}
                </div>
              </div>
            </div>

            <div className="mt-4 flex flex-col gap-2.5">
              {day.exercises.map((rde) => (
                <button
                  key={rde.id}
                  type="button"
                  onClick={() => onExercise(rde.exercise.id)}
                  className="flex w-full items-center gap-3 text-left"
                >
                  <ExerciseThumb name={rde.exercise.name} exerciseId={rde.exercise.id} />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium leading-tight">
                      {rde.exercise.name}
                    </div>
                    <div className="mt-1 font-mono text-[11px] text-gris">
                      {planLabel(rde)}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-3">
            <Card className="flex flex-col p-3">
              <button
                type="button"
                onClick={onTreadmillOpen}
                className="text-left font-mono text-[9px] uppercase tracking-[0.14em] text-blue"
              >
                {es.today.treadmill} ›
              </button>
              <div
                className="mt-1.5 font-mono text-[28px] tabular-nums"
                style={{
                  color: treadmillRunning
                    ? "var(--blue)"
                    : treadmillPaused
                      ? "var(--yellow)"
                      : "var(--ink)",
                }}
              >
                {mmss(treadmillSeconds)}
              </div>
              <div className="mb-2.5 h-4 font-mono text-[11px] text-gris">
                {treadmillPaused
                  ? es.treadmillScreen.paused
                  : treadmillKcal !== null && treadmillSeconds > 0
                    ? es.today.kcal(treadmillKcal)
                    : ""}
              </div>
              <div className="mt-auto flex gap-1.5">
                {(treadmillRunning || treadmillPaused) && (
                  <button
                    type="button"
                    onClick={onTreadmillPause}
                    className="h-touch flex-1 rounded-card border border-line text-[13px]"
                  >
                    {treadmillPaused
                      ? es.treadmillScreen.resume
                      : es.treadmillScreen.pause}
                  </button>
                )}
                <button
                  type="button"
                  onClick={onTreadmillToggle}
                  className="h-touch flex-1 rounded-card border border-ink bg-ink text-[13px] font-medium text-paper"
                >
                  {treadmillRunning || treadmillPaused
                    ? es.today.treadmillStop
                    : es.today.treadmillStart}
                </button>
              </div>
            </Card>

            <Card className="flex flex-col p-3">
              <button
                type="button"
                onClick={onWeightOpen}
                className="text-left font-mono text-[9px] uppercase tracking-[0.14em] text-blue"
              >
                {es.today.bodyweight} ›
              </button>
              <div className="mt-1.5 font-mono text-[28px] tabular-nums">
                {bodyweight?.avg7 != null ? numEs(bodyweight.avg7) : es.today.noData}
              </div>
              <div className="text-xs text-gris">{es.today.weekAverage}</div>
              {bodyweight?.delta_week != null && (
                <div
                  className="mt-1 font-mono text-xs"
                  style={{
                    color:
                      bodyweight.delta_week === 0
                        ? "var(--gris)"
                        : bodyweight.delta_week > 0
                          ? "var(--blue)"
                          : "var(--green)",
                  }}
                >
                  {(bodyweight.delta_week > 0 ? "+" : "") + numEs(bodyweight.delta_week)}{" "}
                  {es.today.vsPrevious}
                </div>
              )}
              <button
                type="button"
                onClick={onLogWeight}
                className="mt-auto h-touch rounded-card border border-line text-[13px]"
              >
                {es.today.logWeight}
              </button>
            </Card>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-2 border-t border-line bg-bg px-4 py-3">
        <Button variant="primary" onClick={onStart} className="w-full">
          {es.actions.start}
        </Button>
        <button
          type="button"
          onClick={onSkip}
          className="h-touch rounded-card border border-line text-sm text-gris"
        >
          {es.today.skip}
        </button>
      </div>
    </div>
  );
}
