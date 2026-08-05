import { useState } from "react";

import { Card } from "../components/Card";
import { ExerciseThumb } from "../components/ExerciseThumb";
import { SetRow } from "../components/SetRow";
import { es } from "../i18n/es";
import { numEs } from "../lib/format";
import {
  doneCount,
  totalSets,
  type ActiveSession,
  type LocalExercise,
} from "../lib/session";

interface SesionProps {
  session: ActiveSession;
  positionLabel: string;
  offline: boolean;
  onWeight: (exerciseIdx: number, setIdx: number, next: number) => void;
  onReps: (exerciseIdx: number, setIdx: number, next: number) => void;
  onCheck: (exerciseIdx: number, setIdx: number) => void;
  onBusy: (exerciseIdx: number) => void;
  onNotes: (value: string) => void;
  onEnd: () => void;
}

function exerciseState(ex: LocalExercise): string {
  const done = ex.sets.filter((s) => s.done).length;
  const first = ex.sets[0];
  const weight = first ? `${numEs(first.weightKg)} ${es.units.kg}` : "";
  const perSide = ex.perSide ? ` · ${es.today.perSide}` : "";
  return `${done} de ${ex.sets.length} ${es.today.sets} · ${weight}${perSide}`;
}

export function Sesion({
  session,
  positionLabel,
  offline,
  onWeight,
  onReps,
  onCheck,
  onBusy,
  onNotes,
  onEnd,
}: SesionProps) {
  const [open, setOpen] = useState(0);

  return (
    <div className="flex h-full flex-col overflow-y-auto px-4 pb-8 pt-4">
      <div className="flex items-start gap-2.5">
        <div className="flex-1">
          <div className="font-display text-[26px] leading-none">{positionLabel}</div>
          <div className="mt-1.5 font-mono text-xs text-gris">
            {es.session.setsProgress(doneCount(session), totalSets(session))}
          </div>
        </div>
        <button
          type="button"
          onClick={onEnd}
          className="h-9 rounded-card border border-line px-3 text-[13px] text-ink"
        >
          {es.actions.endSession}
        </button>
      </div>

      {offline && (
        <div className="mt-3 rounded-field border border-line bg-paper px-3 py-2 font-mono text-[11px] text-gris">
          {es.session.offline}
        </div>
      )}

      <div className="mt-3 flex flex-col gap-3">
        {session.exercises.map((ex, exIdx) => {
          const isOpen = open === exIdx;
          return (
            <Card key={ex.rdeId} className="overflow-hidden">
              <button
                type="button"
                onClick={() => setOpen(isOpen ? -1 : exIdx)}
                className="flex w-full items-center gap-3 p-2.5 text-left"
              >
                <ExerciseThumb name={ex.name} />
                <div className="min-w-0 flex-1">
                  <div className="text-[15px] font-medium leading-tight">{ex.name}</div>
                  {ex.exerciseId !== ex.plannedExerciseId && (
                    <div className="mt-0.5 font-mono text-[10px] text-blue">
                      {es.session.insteadOf(ex.plannedName)}
                    </div>
                  )}
                  <div className="mt-1 font-mono text-[11px] text-gris">
                    {exerciseState(ex)}
                  </div>
                </div>
                <span className="w-4 text-center font-mono text-xs text-gris">
                  {isOpen ? "−" : "+"}
                </span>
              </button>

              {isOpen && (
                <div className="flex flex-col gap-1.5 px-2.5 pb-2.5">
                  {ex.suggestion && (
                    <div
                      className="rounded-r-field px-3 py-2 text-[13px] leading-snug text-ink"
                      style={{
                        background: "rgba(43,95,217,0.08)",
                        borderLeft: "2px solid var(--blue)",
                      }}
                    >
                      {ex.suggestion}
                    </div>
                  )}
                  {ex.sets.map((set, setIdx) => (
                    <SetRow
                      key={set.id}
                      set={set}
                      onWeight={(next) => onWeight(exIdx, setIdx, next)}
                      onReps={(next) => onReps(exIdx, setIdx, next)}
                      onCheck={() => onCheck(exIdx, setIdx)}
                    />
                  ))}
                  <button
                    type="button"
                    onClick={() => onBusy(exIdx)}
                    className="mt-1 h-touch rounded-card border border-line text-sm text-ink"
                  >
                    {es.actions.busy}
                  </button>
                </div>
              )}
            </Card>
          );
        })}
      </div>

      <div className="mt-3 flex flex-col gap-1">
        <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
          {es.session.notesLabel}
        </span>
        <textarea
          value={session.notes}
          onChange={(e) => onNotes(e.target.value)}
          placeholder={es.session.notesPlaceholder}
          className="min-h-[64px] rounded-card border border-line bg-paper p-3 text-sm text-ink"
        />
      </div>
    </div>
  );
}
