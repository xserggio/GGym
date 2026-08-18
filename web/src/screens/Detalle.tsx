import { useEffect, useState } from "react";

import { BarbellChart } from "../components/BarbellChart";
import { Button } from "../components/Button";
import { Header } from "../components/Header";
import { es } from "../i18n/es";
import {
  api,
  type ExerciseHistoryEntry,
  type ExerciseOut,
} from "../lib/api";
import { dateShortEs, numEs } from "../lib/format";
import { equipmentLabel, patternLabel } from "../lib/labels";

interface DetalleProps {
  exerciseId: string;
  onBack: () => void;
}

const oneRm = (e: ExerciseHistoryEntry) => e.weight_kg * (1 + e.reps / 30);

export function Detalle({ exerciseId, onBack }: DetalleProps) {
  const [exercise, setExercise] = useState<ExerciseOut | null>(null);
  const [history, setHistory] = useState<ExerciseHistoryEntry[]>([]);
  const [imgFailed, setImgFailed] = useState(false);

  useEffect(() => {
    setImgFailed(false);
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

  // The API defaults these to [], but the generated type marks them optional.
  const technique = exercise.technique ?? [];
  const mistakes = exercise.mistakes ?? [];
  const weights = history.map((h) => h.weight_kg);
  const min = weights.length ? Math.min(...weights) - 2.5 : 0;
  const max = weights.length ? Math.max(...weights) + 2.5 : 1;
  const span = max - min || 1;
  const prIndex =
    history.length > 0
      ? history.reduce((best, h, i) => (oneRm(h) > oneRm(history[best]!) ? i : best), 0)
      : -1;

  return (
    <div className="h-full overflow-y-auto pb-6"
      style={{ paddingBottom: "calc(1.5rem + var(--safe-bottom))" }}
    >
      {/* Own bar, not an overlay: on top of the photo the button was unreadable. */}
      <Header
        eyebrow={patternLabel(exercise.pattern)}
        title={exercise.name}
        leading={
          <Button variant="ghost" onClick={onBack} className="mb-1 !min-h-0 !px-3 !py-1.5">
            {es.actions.back}
          </Button>
        }
      />

      {/* Duotone exercise photo; hatched marker shows if the image is missing. */}
      <div
        className="relative flex aspect-[4/3] w-full items-end overflow-hidden p-3"
        style={{
          background:
            "repeating-linear-gradient(135deg, var(--thumbA) 0 5px, var(--thumbB) 5px 10px)",
        }}
      >
        {!imgFailed && (
          <img
            src={`${import.meta.env.BASE_URL}exercises/${exerciseId}.webp`}
            alt={exercise.name}
            onError={() => setImgFailed(true)}
            className="absolute inset-0 h-full w-full object-cover"
          />
        )}
        {imgFailed && (
          <span className="font-mono text-[10px] text-gris">
            {es.detail.photoNote} · {exercise.name}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-4 px-4 pt-4">
        <div className="font-mono text-[11px] text-gris">
          {equipmentLabel(exercise.equipment)}
          {exercise.per_side ? ` · ${es.today.perSide}` : ""}
        </div>

        {exercise.description && (
          <p className="text-[15px] leading-relaxed">{exercise.description}</p>
        )}

        {technique.length > 0 && (
          <section>
            <div className="mb-2 font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
              {es.detail.technique}
            </div>
            <ol className="flex flex-col gap-2.5">
              {technique.map((step, i) => (
                <li key={i} className="flex gap-3">
                  <span className="mt-[3px] flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-chip border border-line font-mono text-[10px] text-gris">
                    {i + 1}
                  </span>
                  <span className="text-[14px] leading-snug">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        )}

        {mistakes.length > 0 && (
          <section>
            <div className="mb-2 font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
              {es.detail.mistakes}
            </div>
            <ul className="flex flex-col gap-2.5">
              {mistakes.map((item, i) => (
                <li key={i} className="flex gap-3">
                  {/* Amber, not red: these cost you reps, they are not alarms. */}
                  <span
                    className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full"
                    style={{ background: "var(--yellow)" }}
                  />
                  <span className="text-[14px] leading-snug">{item}</span>
                </li>
              ))}
            </ul>
          </section>
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
