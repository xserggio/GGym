import { useEffect, useState } from "react";

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
 * −/+ stepper with 44px touch targets (spec §6). The centre is a real input, so
 * a value can also be typed (Spanish comma accepted) — quicker than tapping +
 * many times. Used one-handed, sweaty; figures are monospaced and tabular.
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
  const [text, setText] = useState(() => numEs(value));

  // Keep the field in sync when the value changes via the buttons or a re-render.
  useEffect(() => setText(numEs(value)), [value]);

  const commit = () => {
    const parsed = Number.parseFloat(text.replace(",", "."));
    if (Number.isFinite(parsed)) onChange(clamp(parsed));
    else setText(numEs(value));
  };

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
      <input
        inputMode="decimal"
        aria-label={`${label}: ${numEs(value)}`}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") e.currentTarget.blur();
        }}
        style={{ width: valueWidth }}
        className="h-touch border-y border-line bg-paper text-center font-mono text-lg tabular-nums text-ink outline-none"
      />
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
