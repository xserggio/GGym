import { BAR_KG, platesPerSide } from "../lib/barbell";

interface BarbellChartProps {
  weightKg: number;
  barKg?: number;
  /** Compact rows (session/history) use smaller discs than list/hero. */
  compact?: boolean;
  className?: string;
}

const PLATE_BORDER = "1px solid rgba(20,22,26,0.5)";

/**
 * Schematic loaded barbell: plates mirrored around a central sleeve, coloured by
 * the IWF code. Heights/widths come from the token discs in lib/barbell. Dynamic
 * per-plate colour and height mean inline styles here by design.
 */
export function BarbellChart({
  weightKg,
  barKg = BAR_KG,
  compact = false,
  className,
}: BarbellChartProps) {
  const plates = platesPerSide(weightKg, barKg); // largest -> smallest
  const width = compact ? 3 : 4;
  const sleeve = compact ? 10 : 12;
  const scale = compact ? 0.72 : 1;

  const disc = (height: number, color: string, key: string) => (
    <span
      key={key}
      style={{
        display: "block",
        width,
        height: Math.round(height * scale),
        background: color,
        border: PLATE_BORDER,
        borderRadius: 1,
        boxSizing: "border-box",
      }}
    />
  );

  return (
    <span
      role="img"
      aria-label={`${numLabel(weightKg)} kg`}
      className={className}
      style={{ display: "inline-flex", alignItems: "center", gap: 1 }}
    >
      {[...plates]
        .reverse()
        .map((p, i) => disc(p.height, p.color, `l${i}`))}
      <span style={{ display: "block", width: sleeve, height: 2, background: "var(--gris)" }} />
      {plates.map((p, i) => disc(p.height, p.color, `r${i}`))}
    </span>
  );
}

function numLabel(value: number): string {
  return String(value).replace(".", ",");
}
