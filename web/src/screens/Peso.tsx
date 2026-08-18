import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Header } from "../components/Header";
import { es } from "../i18n/es";
import type { BodyWeightSummary } from "../lib/api";
import { dateShortEs, numEs } from "../lib/format";

interface PesoProps {
  data: BodyWeightSummary | null;
  onLog: () => void;
  onBack: () => void;
}

export function Peso({ data, onLog, onBack }: PesoProps) {
  const points = data?.points ?? [];
  const weights = points.map((p) => p.weight_kg);
  const min = weights.length ? Math.min(...weights) - 0.5 : 0;
  const max = weights.length ? Math.max(...weights) + 0.5 : 1;
  const span = max - min || 1;
  const delta = data?.delta_week ?? null;
  // Neither direction is "good" without knowing the goal, so the trend is
  // marked, not judged: up is blue, down is green only as a visual pair.
  const deltaColor =
    delta === null || delta === 0
      ? "var(--gris)"
      : delta > 0
        ? "var(--blue)"
        : "var(--green)";

  return (
    <div className="h-full overflow-y-auto pb-6"
      style={{ paddingBottom: "calc(1.5rem + var(--safe-bottom))" }}
    >
      <Header
        title={es.weightScreen.title}
        leading={
          <Button variant="ghost" onClick={onBack} className="mb-1 !min-h-0 !px-3 !py-1.5">
            {es.actions.back}
          </Button>
        }
      />

      <div className="flex flex-col gap-4 px-4 pt-4">
        <Card className="p-4">
          <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
            {es.weightScreen.current}
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="font-display text-[48px] leading-none">
              {data?.avg7 != null ? numEs(data.avg7) : "—"}
            </span>
            <span className="font-mono text-sm text-gris">kg</span>
          </div>
          {delta !== null && (
            <div className="mt-2 font-mono text-sm" style={{ color: deltaColor }}>
              {delta > 0 ? "+" : ""}
              {numEs(delta)} kg · {es.weightScreen.delta}
            </div>
          )}
          {data?.latest != null && (
            <div className="mt-1 font-mono text-[11px] text-gris">
              {es.weightScreen.latest}: {numEs(data.latest)} kg
            </div>
          )}
          <p className="mt-3 text-[12px] leading-snug text-gris">
            {es.weightScreen.hint}
          </p>
          <Button variant="secondary" onClick={onLog} className="mt-3 w-full">
            {es.weightScreen.add}
          </Button>
        </Card>

        <Card className="p-4">
          <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
            {es.weightScreen.history}
          </div>
          {points.length === 0 ? (
            <p className="mt-2 text-sm text-gris">{es.weightScreen.empty}</p>
          ) : (
            <>
              <div className="mb-4 mt-3 flex h-24 items-end gap-1">
                {points.map((p, i) => (
                  <div key={i} className="flex flex-1 flex-col justify-end">
                    <span
                      className="w-full rounded-t-[2px]"
                      style={{
                        height: `${Math.max(4, ((p.weight_kg - min) / span) * 100)}%`,
                        background: "var(--green)",
                        opacity: 0.35 + (0.65 * (i + 1)) / points.length,
                      }}
                    />
                  </div>
                ))}
              </div>
              <div className="flex flex-col">
                {[...points].reverse().map((p, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 border-t border-line py-2 first:border-t-0"
                  >
                    <span className="w-14 font-mono text-[11px] text-gris">
                      {dateShortEs(p.measured_on)}
                    </span>
                    <span className="ml-auto font-mono text-sm tabular-nums">
                      {numEs(p.weight_kg)} kg
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
