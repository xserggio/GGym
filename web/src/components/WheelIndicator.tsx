/**
 * The wheel: five marks with the current position highlighted. Not a calendar —
 * it never shows days of the week (spec §5.1, brief).
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
            className={`flex h-[18px] w-[18px] items-center justify-center rounded-chip border border-line font-mono text-[10px] ${
              active ? "bg-ink text-bg" : "text-gris"
            }`}
          >
            {n}
          </span>
        );
      })}
    </div>
  );
}
