import { useEffect, useState } from "react";

import { BarbellChart } from "../components/BarbellChart";
import { Button } from "../components/Button";
import { es } from "../i18n/es";
import {
  api,
  type ExerciseHistoryEntry,
  type ExerciseOut,
} from "../lib/api";
import { dateShortEs, numEs } from "../lib/format";

interface DetalleProps {
  exerciseId: string;
  onBack: () => void;
}

const patternLabel = (p: string) => p.replace(/_/g, " ");
const oneRm = (e: ExerciseHistoryEntry) => e.weight_kg * (1 + e.reps / 30);

export function Detalle({ exerciseId, onBack }: DetalleProps) {
  const [exercise, setExercise] = useState<ExerciseOut | null>(null);
  const [history, setHistory] = useState<ExerciseHistoryEntry[]>([]);

  useEffect(() => {
    api.exercise(exerciseId).then(setExercise).catch(() => undefined);
    api.exerciseHistory(exerciseId).then(setHistory).catch(() => undefined);
  }, [exerciseId]);

  if (!exercise) {
    return (
      <div className="flex h-full items-center justify-center font-mono text-xs text-gris">
        …
      </div>
    );
  }

  const weights = history.map((h) => h.weight_kg);
  const min = weights.length ? Math.min(...weights) - 2.5 : 0;
  const max = weights.length ? Math.max(...weights) + 2.5 : 1;
  const span = max - min || 1;
  const prIndex =
    history.length > 0
      ? history.reduce((best, h, i) => (oneRm(h) > oneRm(history[best]!) ? i : best), 0)
      : -1;

  return (
    <div className="h-full overflow-y-auto pb-6">
      {/* Photo placeholder (real images later), duotono treatment */}
      <div
        className="relative flex aspect-[4/3] w-full items-end p-3"
        style={{
          background:
            "repeating-linear-gradient(135deg, var(--thumbA) 0 5px, var(--thumbB) 5px 10px)",
        }}
      >
        <span className="font-mono text-[10px] text-gris">
          {es.detail.photoNote} · {exercise.name}
        </span>
        <Button
          variant="ghost"
          onClick={onBack}
          className="absolute left-3 top-3 !min-h-0 bg-paper !px-3 !py-1.5"
        >
          {es.actions.back}
        </Button>
      </div>

      <div className="flex flex-col gap-4 px-4 pt-4">
        <div>
          <h1 className="font-display text-3xl leading-tight">{exercise.name}</h1>
          <div className="mt-1 font-mono text-[11px] text-gris">
            {patternLabel(exercise.pattern)} · {exercise.equipment}
            {exercise.per_side ? ` · ${es.today.perSide}` : ""}
          </div>
        </div>

        {exercise.description && (
          <p className="text-[15px] leading-relaxed">{exercise.description}</p>
        )}

        <div className="rounded-card border border-line p-4">
          <div className="mb-3 font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
            {es.detail.weightHistory}
          </div>

          {history.length === 0 ? (
            <p className="text-sm text-gris">{es.detail.empty}</p>
          ) : (
            <>
              <div className="mb-4 flex h-16 items-end gap-1.5">
                {history.map((h, i) => (
                  <div key={i} className="flex flex-1 flex-col justify-end">
                    <span
                      className="w-full rounded-t-[2px]"
                      style={{
                        height: `${Math.max(6, ((h.weight_kg - min) / span) * 100)}%`,
                        background: i === prIndex ? "var(--red)" : "var(--blue)",
                      }}
                    />
                  </div>
                ))}
              </div>

              <div className="flex flex-col">
                {[...history].reverse().map((h, i) => {
                  const isPr = history.length - 1 - i === prIndex;
                  return (
                    <div
                      key={i}
                      className="flex items-center gap-3 border-t border-line py-2.5 first:border-t-0"
                    >
                      <span className="w-12 font-mono text-[11px] text-gris">
                        {dateShortEs(h.session_on)}
                      </span>
                      <BarbellChart weightKg={h.weight_kg} compact />
                      <span className="ml-auto font-mono text-sm tabular-nums">
                        {numEs(h.weight_kg)} × {h.reps}
                      </span>
                      <span className="w-6 text-right font-mono text-[10px] text-red">
                        {isPr ? es.detail.pr : ""}
                      </span>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
