import { BarbellChart } from "../components/BarbellChart";
import { Button } from "../components/Button";
import { es } from "../i18n/es";
import type { SessionSummary } from "../lib/session";
import { numEs } from "../lib/format";

interface HighlightsProps {
  summary: SessionSummary;
  onDone: () => void;
}

function volumeLabel(kg: number): { value: string; unit: string } {
  if (kg >= 1000) return { value: numEs(Math.round(kg / 100) / 10), unit: "t" };
  return { value: numEs(Math.round(kg)), unit: "kg" };
}

function Kpi({
  label,
  value,
  unit,
}: {
  label: string;
  value: string;
  unit: string;
}) {
  return (
    <div className="flex flex-col gap-1 bg-bg px-4 py-5">
      <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-gris">
        {label}
      </span>
      <div className="flex items-baseline gap-1.5">
        <span className="font-display text-[42px] leading-none tracking-tight">
          {value}
        </span>
        <span className="font-mono text-[13px] text-gris">{unit}</span>
      </div>
    </div>
  );
}

export function Highlights({ summary, onDone }: HighlightsProps) {
  const volume = volumeLabel(summary.volumeKg);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-4 pb-6 pt-8">
        <header className="mb-5">
          <h1 className="font-display text-[34px] leading-tight">
            {es.highlights.title}
          </h1>
          <div className="mt-1 font-mono text-[12px] text-gris">
            {summary.positionLabel}
          </div>
        </header>

        <div className="grid grid-cols-2 gap-[1px] rounded-card bg-line">
          <Kpi
            label={es.highlights.duration}
            value={String(summary.durationMin)}
            unit={es.highlights.min}
          />
          <Kpi label={es.highlights.volume} value={volume.value} unit={volume.unit} />
          <Kpi
            label={es.highlights.sets}
            value={String(summary.setsDone)}
            unit={es.today.sets}
          />
          <Kpi
            label={es.highlights.kcal}
            value={summary.kcal == null ? "—" : String(summary.kcal)}
            unit={summary.kcal == null ? "" : `kcal ${es.highlights.approx}`}
          />
        </div>

        {summary.exercises.length > 0 && (
          <div className="mt-6">
            <div className="mb-1 font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
              {es.highlights.bestSet}
            </div>
            {summary.exercises.map((ex, i) => (
              <div
                key={i}
                className="flex items-center gap-3 border-b border-line py-2.5"
              >
                <span className="min-w-0 flex-1 truncate text-sm">{ex.name}</span>
                <BarbellChart weightKg={ex.weightKg} compact />
                <span className="font-mono text-sm tabular-nums">
                  {numEs(ex.weightKg)} × {ex.reps}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-line bg-bg px-4 py-3">
        <Button variant="primary" onClick={onDone} className="w-full">
          {es.highlights.done}
        </Button>
      </div>
    </div>
  );
}
