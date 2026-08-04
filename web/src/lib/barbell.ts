/**
 * The loaded barbell — the signature element of the design (brief). Given a
 * total weight it computes the plates on ONE side, using an olympic 20 kg bar
 * and the IWF competition colour code. Greedy, largest plate first. This mirrors
 * the prototype's `platesFor`; the colours and heights come straight from it.
 */
export interface PlateSpec {
  kg: number;
  /** CSS colour (hex or var()). */
  color: string;
  /** Reference disc height in px, used by the chart to scale plates. */
  height: number;
}

export const BAR_KG = 20;

/** Ordered largest -> smallest, matching the prototype's PLATES table. */
export const PLATES: readonly PlateSpec[] = [
  { kg: 25, color: "#d2333c", height: 24 },
  { kg: 20, color: "#2b5fd9", height: 21 },
  { kg: 15, color: "#f2c230", height: 18 },
  { kg: 10, color: "#2e8b57", height: 15 },
  { kg: 5, color: "var(--plate5)", height: 12 },
  { kg: 2.5, color: "#d2333c", height: 9 },
  { kg: 1.25, color: "var(--plate-grey)", height: 7 },
];

/**
 * Plates loaded on one side of the bar, largest first. Empty when the weight is
 * at or below the bar, or cannot be represented with available plates.
 */
export function platesPerSide(totalKg: number, barKg: number = BAR_KG): PlateSpec[] {
  let perSide = (totalKg - barKg) / 2;
  const out: PlateSpec[] = [];
  if (perSide <= 0) return out;
  for (const plate of PLATES) {
    while (perSide >= plate.kg - 0.001) {
      out.push(plate);
      perSide = Math.round((perSide - plate.kg) * 100) / 100;
    }
  }
  return out;
}
