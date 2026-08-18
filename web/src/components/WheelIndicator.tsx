import { sessionColor } from "../lib/palette";

/**
 * The wheel: five marks with the current position highlighted. Not a calendar —
 * it never shows days of the week (spec §5.1, brief). The active mark carries
 * that session's identity colour, the same one used wherever the session is
 * named elsewhere.
 */
interface WheelIndicatorProps {
  positions: number;
  current: number;
}

export function WheelIndicator({ positions, current }: WheelIndicatorProps) {
  return (
    <div className="flex items-center gap-1.5" aria-label={`posición ${current} de ${positions}`}>
      {Array.from({ length: positions }, (_, i) => i + 1).map((n) => {
        const active = n === current;
        return (
          <span
            key={n}
            className="flex h-[18px] w-[18px] items-center justify-center rounded-chip border font-mono text-[10px]"
            style={
              active
                ? {
                    background: sessionColor(n),
                    borderColor: sessionColor(n),
                    color: "var(--paper)",
                  }
                : { borderColor: "var(--line)", color: "var(--gris)" }
            }
          >
            {n}
          </span>
        );
      })}
    </div>
  );
}
