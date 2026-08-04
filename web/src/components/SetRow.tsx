import { es } from "../i18n/es";
import type { LocalSet } from "../lib/session";
import { BarbellChart } from "./BarbellChart";
import { NumberStepper } from "./NumberStepper";

interface SetRowProps {
  set: LocalSet;
  onWeight: (next: number) => void;
  onReps: (next: number) => void;
  onCheck: () => void;
}

/**
 * The most important component in the app (brief): set number, weight, reps and
 * a big check. On check the row fills green and (phase 5) the rest timer starts.
 */
export function SetRow({ set, onWeight, onReps, onCheck }: SetRowProps) {
  return (
    <div
      className="flex items-center gap-1 rounded-card p-1.5"
      style={{
        borderLeft: `3px solid ${set.done ? "var(--green)" : "transparent"}`,
        backgroundColor: set.done ? "var(--tint)" : "var(--bg)",
        animation: set.done ? "fillRight 180ms ease-out" : "none",
      }}
    >
      <span className="w-[18px] text-center font-mono text-sm text-gris">
        {set.setNumber}
      </span>

      <div className="flex flex-col items-center gap-0.5">
        <NumberStepper
          label={es.session.weight}
          value={set.weightKg}
          step={2.5}
          onChange={onWeight}
        />
        <BarbellChart weightKg={set.weightKg} compact />
      </div>

      <NumberStepper
        label={es.session.reps}
        value={set.reps}
        step={1}
        min={1}
        onChange={onReps}
        valueWidth={34}
      />

      <button
        type="button"
        aria-label={`serie ${set.setNumber}: marcar`}
        aria-pressed={set.done}
        onClick={onCheck}
        className="ml-auto flex h-touch w-touch items-center justify-center rounded-field text-lg leading-none"
        style={{
          border: `1px solid ${set.done ? "var(--green)" : "var(--line)"}`,
          background: set.done ? "var(--green)" : "transparent",
          color: set.done ? "var(--paper)" : "var(--gris)",
        }}
      >
        ✓
      </button>
    </div>
  );
}
