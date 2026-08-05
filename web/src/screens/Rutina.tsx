import { useEffect, useState } from "react";

import { BottomSheet } from "../components/BottomSheet";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { es } from "../i18n/es";
import {
  api,
  type ExerciseSummary,
  type RoutineDayExerciseOut,
  type RoutineOut,
} from "../lib/api";

interface RutinaProps {
  onSettings: () => void;
}

type Field = "target_sets" | "rep_min" | "rep_max" | "rest_s";

function move<T>(arr: T[], index: number, dir: -1 | 1): T[] | null {
  const j = index + dir;
  if (j < 0 || j >= arr.length) return null;
  const copy = [...arr];
  const a = copy[index]!;
  copy[index] = copy[j]!;
  copy[j] = a;
  return copy;
}

function MiniStepper({
  label,
  value,
  min,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  step: number;
  onChange: (next: number) => void;
}) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-gris">
        {label}
      </span>
      <div className="flex items-center">
        <button
          type="button"
          aria-label={`${label}: menos`}
          onClick={() => onChange(Math.max(min, value - step))}
          className="h-9 w-7 rounded-l-field border border-line bg-paper font-mono text-base text-ink"
        >
          −
        </button>
        <span className="h-9 w-10 border-y border-line bg-paper text-center font-mono text-sm leading-9 tabular-nums">
          {value}
        </span>
        <button
          type="button"
          aria-label={`${label}: más`}
          onClick={() => onChange(value + step)}
          className="h-9 w-7 rounded-r-field border border-line bg-paper font-mono text-base text-ink"
        >
          +
        </button>
      </div>
    </div>
  );
}

function ReorderButtons({
  onUp,
  onDown,
  disabledUp,
  disabledDown,
}: {
  onUp: () => void;
  onDown: () => void;
  disabledUp: boolean;
  disabledDown: boolean;
}) {
  const cls =
    "h-8 w-8 rounded-field border border-line bg-paper font-mono text-sm text-ink disabled:opacity-30";
  return (
    <div className="flex gap-1">
      <button type="button" aria-label="subir" onClick={onUp} disabled={disabledUp} className={cls}>
        ↑
      </button>
      <button
        type="button"
        aria-label="bajar"
        onClick={onDown}
        disabled={disabledDown}
        className={cls}
      >
        ↓
      </button>
    </div>
  );
}

export function Rutina({ onSettings }: RutinaProps) {
  const [routine, setRoutine] = useState<RoutineOut | null>(null);
  const [openDay, setOpenDay] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<ExerciseSummary[]>([]);
  const [addDayId, setAddDayId] = useState<string | null>(null);

  useEffect(() => {
    api.routine().then((r) => {
      setRoutine(r);
      setOpenDay(r.days[0]?.id ?? null);
    });
    api.exercises().then(setCatalog);
  }, []);

  if (!routine) {
    return (
      <div className="flex h-full items-center justify-center font-mono text-xs text-gris">
        …
      </div>
    );
  }

  const patchField = (dayId: string, ex: RoutineDayExerciseOut, field: Field, value: number) => {
    // optimistic local update, then persist the full row
    setRoutine((r) =>
      r
        ? {
            ...r,
            days: r.days.map((d) =>
              d.id !== dayId
                ? d
                : {
                    ...d,
                    exercises: d.exercises.map((e) =>
                      e.id === ex.id ? { ...e, [field]: value } : e,
                    ),
                  },
            ),
          }
        : r,
    );
    const body = {
      target_sets: ex.target_sets,
      rep_min: ex.rep_min,
      rep_max: ex.rep_max,
      rest_s: ex.rest_s,
      [field]: value,
    };
    void api.updateExercise(ex.id, body).catch(() => api.routine().then(setRoutine));
  };

  const reorderEx = (dayId: string, ids: string[]) =>
    void api.reorderExercises(dayId, ids).then(setRoutine);
  const reorderDays = (ids: string[]) => void api.reorderDays(ids).then(setRoutine);
  const removeEx = (rdeId: string) => void api.removeExercise(rdeId).then(setRoutine);
  const renameDay = (dayId: string, name: string) =>
    void api.renameDay(dayId, name).then(setRoutine);
  const addEx = (dayId: string, exId: string) =>
    void api.addExercise(dayId, exId).then((r) => {
      setRoutine(r);
      setAddDayId(null);
    });

  return (
    <div className="h-full overflow-y-auto px-4 pb-6 pt-4">
      <header className="mb-2 flex items-center">
        <h1 className="font-display text-3xl">{es.routine.title}</h1>
        <Button variant="ghost" onClick={onSettings} className="ml-auto !min-h-0 !px-3 !py-1.5">
          {es.actions.settings}
        </Button>
      </header>
      <p className="mb-3 text-[13px] text-gris">{es.routine.hint}</p>

      <div className="flex flex-col gap-3">
        {routine.days.map((day, dayIdx) => {
          const isOpen = openDay === day.id;
          const dayIds = routine.days.map((d) => d.id);
          return (
            <Card key={day.id} className="p-3">
              <div className="flex items-center gap-2">
                <span className="flex h-5 w-5 items-center justify-center rounded-chip bg-ink font-mono text-[11px] text-bg">
                  {day.position}
                </span>
                <button
                  type="button"
                  onClick={() => setOpenDay(isOpen ? null : day.id)}
                  className="min-w-0 flex-1 text-left"
                >
                  <div className="truncate text-[15px] font-medium">{day.name}</div>
                  <div className="font-mono text-[11px] text-gris">
                    {day.exercises.length} {es.today.exercises}
                  </div>
                </button>
                <ReorderButtons
                  onUp={() => {
                    const next = move(dayIds, dayIdx, -1);
                    if (next) reorderDays(next);
                  }}
                  onDown={() => {
                    const next = move(dayIds, dayIdx, 1);
                    if (next) reorderDays(next);
                  }}
                  disabledUp={dayIdx === 0}
                  disabledDown={dayIdx === routine.days.length - 1}
                />
              </div>

              {isOpen && (
                <div className="mt-3 flex flex-col gap-2">
                  <input
                    key={day.name}
                    defaultValue={day.name}
                    aria-label="nombre de la sesión"
                    onBlur={(e) => {
                      const v = e.target.value.trim();
                      if (v && v !== day.name) renameDay(day.id, v);
                    }}
                    className="h-touch w-full rounded-field border border-line bg-paper px-3 text-sm font-medium text-ink"
                  />
                  {day.exercises.length === 0 && (
                    <p className="text-[13px] text-gris">{es.routine.empty}</p>
                  )}
                  {day.exercises.map((ex, exIdx) => {
                    const exIds = day.exercises.map((e) => e.id);
                    return (
                      <div key={ex.id} className="rounded-field border border-line p-2.5">
                        <div className="flex items-center gap-2">
                          <span className="min-w-0 flex-1 truncate text-sm font-medium">
                            {ex.exercise.name}
                          </span>
                          <ReorderButtons
                            onUp={() => {
                              const next = move(exIds, exIdx, -1);
                              if (next) reorderEx(day.id, next);
                            }}
                            onDown={() => {
                              const next = move(exIds, exIdx, 1);
                              if (next) reorderEx(day.id, next);
                            }}
                            disabledUp={exIdx === 0}
                            disabledDown={exIdx === day.exercises.length - 1}
                          />
                          <button
                            type="button"
                            aria-label={es.routine.remove}
                            onClick={() => removeEx(ex.id)}
                            className="h-8 w-8 rounded-field border border-line bg-paper text-sm text-red"
                          >
                            ×
                          </button>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-3">
                          <MiniStepper
                            label={es.routine.sets}
                            value={ex.target_sets}
                            min={1}
                            step={1}
                            onChange={(v) => patchField(day.id, ex, "target_sets", v)}
                          />
                          <MiniStepper
                            label="rep min"
                            value={ex.rep_min}
                            min={1}
                            step={1}
                            onChange={(v) => patchField(day.id, ex, "rep_min", v)}
                          />
                          <MiniStepper
                            label="rep máx"
                            value={ex.rep_max}
                            min={1}
                            step={1}
                            onChange={(v) => patchField(day.id, ex, "rep_max", v)}
                          />
                          <MiniStepper
                            label={es.routine.rest}
                            value={ex.rest_s}
                            min={15}
                            step={15}
                            onChange={(v) => patchField(day.id, ex, "rest_s", v)}
                          />
                        </div>
                      </div>
                    );
                  })}
                  <button
                    type="button"
                    onClick={() => setAddDayId(day.id)}
                    className="h-touch rounded-field border border-line text-sm text-ink"
                  >
                    {es.routine.add}
                  </button>
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {addDayId && (
        <BottomSheet title={es.routine.addTitle} onClose={() => setAddDayId(null)}>
          <div className="flex flex-col gap-1.5">
            {catalog.map((ex) => (
              <button
                key={ex.id}
                type="button"
                onClick={() => addEx(addDayId, ex.id)}
                className="flex items-center gap-2 rounded-field border border-line bg-paper p-2.5 text-left"
              >
                <span className="flex-1 text-sm">{ex.name}</span>
                <span className="font-mono text-[10px] text-gris">
                  {ex.pattern.replace(/_/g, " ")}
                </span>
              </button>
            ))}
          </div>
        </BottomSheet>
      )}
    </div>
  );
}
