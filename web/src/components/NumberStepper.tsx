import { numEs } from "../lib/format";

interface NumberStepperProps {
  value: number;
  step: number;
  min?: number;
  onChange: (next: number) => void;
  /** Accessible label, e.g. "peso" or "reps". */
  label: string;
  /** Width of the value box in px (weights need more room than reps). */
  valueWidth?: number;
}

/**
 * −/+ stepper with 44px touch targets (spec §6). Used one-handed, sweaty; the
 * value is monospaced with tabular figures so it never shifts.
 */
export function NumberStepper({
  value,
  step,
  min = 0,
  onChange,
  label,
  valueWidth = 48,
}: NumberStepperProps) {
  const clamp = (n: number) => Math.max(min, Math.round(n * 100) / 100);
  return (
    <div className="flex items-center">
      <button
        type="button"
        aria-label={`${label}: menos`}
        onClick={() => onChange(clamp(value - step))}
        className="h-touch w-[30px] rounded-l-field border border-line bg-paper font-mono text-lg text-ink"
      >
        −
      </button>
      <span
        aria-label={`${label}: ${numEs(value)}`}
        style={{ width: valueWidth }}
        className="h-touch border-y border-line bg-paper text-center font-mono text-lg leading-[42px] tabular-nums"
      >
        {numEs(value)}
      </span>
      <button
        type="button"
        aria-label={`${label}: más`}
        onClick={() => onChange(clamp(value + step))}
        className="h-touch w-[30px] rounded-r-field border border-line bg-paper font-mono text-lg text-ink"
      >
        +
      </button>
    </div>
  );
}
