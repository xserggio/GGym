import { es } from "../i18n/es";

export type Period = "7d" | "30d" | "365d" | "all";

export const PERIODS: Period[] = ["7d", "30d", "365d", "all"];

interface PeriodTabsProps {
  value: Period;
  onChange: (period: Period) => void;
}

/**
 * Window selector for the totals. Marked with the same short ink rule the
 * header uses rather than a filled pill, so the two read as one system.
 */
export function PeriodTabs({ value, onChange }: PeriodTabsProps) {
  return (
    <div className="flex items-center gap-4">
      {PERIODS.map((period) => {
        const active = period === value;
        return (
          <button
            key={period}
            type="button"
            onClick={() => onChange(period)}
            className="flex flex-col items-center gap-1 pb-0.5"
            style={{ color: active ? "var(--ink)" : "var(--gris)" }}
          >
            <span className="font-mono text-[11px] tracking-[0.04em]">
              {es.periods[period]}
            </span>
            <span
              className="h-[2px] w-full"
              style={{ background: active ? "var(--ink)" : "transparent" }}
            />
          </button>
        );
      })}
    </div>
  );
}
