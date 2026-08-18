import { es } from "../i18n/es";
import { sessionColor } from "../lib/palette";

interface WheelStripProps {
  positions: number;
  current: number;
}

/**
 * The wheel as a track rather than a row of chips: every position side by side,
 * the current one filled with its session colour. It moved out of the masthead
 * so the title can sit on the centre axis, and the wider format has room to say
 * what it is — the rotation, not a calendar (spec §5.1).
 */
export function WheelStrip({ positions, current }: WheelStripProps) {
  return (
    <div className="flex items-center gap-2.5 px-4 pt-3">
      <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
        {es.today.wheel}
      </span>
      <div
        className="flex flex-1 overflow-hidden rounded-chip border border-line"
        aria-label={`posición ${current} de ${positions}`}
      >
        {Array.from({ length: positions }, (_, i) => i + 1).map((n) => {
          const active = n === current;
          return (
            <span
              key={n}
              className="flex-1 border-l border-line py-1 text-center font-mono text-[11px] first:border-l-0"
              style={{
                background: active ? sessionColor(n) : "transparent",
                color: active ? "var(--paper)" : "var(--gris)",
              }}
            >
              {n}
            </span>
          );
        })}
      </div>
    </div>
  );
}
