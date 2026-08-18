/**
 * Colour for data, never for decoration.
 *
 * The app is ink on cement by design (brief), so colour has to earn its place.
 * It reuses the IWF plate code the barbell chart already speaks — red 25, blue
 * 20, yellow 15, green 10 — which is the gym's own colour language rather than
 * an arbitrary chart palette. Backgrounds and text stay monochrome; only
 * measured values get a hue, and the same pattern always gets the same one.
 */
const PLATE_CYCLE = [
  "var(--red)",
  "var(--blue)",
  "var(--yellow)",
  "var(--green)",
] as const;

/** Stable colour per movement pattern, grouped so related work reads alike. */
const PATTERN_COLOR: Record<string, string> = {
  // Push
  empuje_horizontal: "var(--red)",
  empuje_vertical: "var(--red)",
  triceps: "var(--red)",
  // Pull
  tiron_horizontal: "var(--blue)",
  tiron_vertical: "var(--blue)",
  biceps: "var(--blue)",
  deltoides_lateral: "var(--blue)",
  // Legs
  cuadriceps: "var(--green)",
  cadena_posterior: "var(--green)",
  gluteo: "var(--green)",
  gemelo: "var(--green)",
  abduccion: "var(--green)",
  // Core
  core: "var(--yellow)",
};

/**
 * Identity colour per wheel position, in plate order (25, 20, 15, 10, then the
 * grey change plate). Each session keeps its colour everywhere — the wheel dots,
 * the "next up" card, the routine editor — so "today is the blue one" becomes a
 * usable shorthand instead of decoration.
 */
const SESSION_COLORS = [
  "var(--red)",
  "var(--blue)",
  "var(--yellow)",
  "var(--green)",
  "var(--plate-grey)",
] as const;

export function sessionColor(position: number): string {
  const index = (Math.max(1, position) - 1) % SESSION_COLORS.length;
  return SESSION_COLORS[index]!;
}

export function patternColor(pattern: string): string {
  const known = PATTERN_COLOR[pattern];
  if (known) return known;
  // Unknown pattern (added server-side): pick deterministically so it stays put
  // between renders instead of flickering.
  let hash = 0;
  for (let i = 0; i < pattern.length; i += 1) hash = (hash * 31 + pattern.charCodeAt(i)) | 0;
  return PLATE_CYCLE[Math.abs(hash) % PLATE_CYCLE.length]!;
}

/**
 * Traffic light for weekly sets per muscle group: the useful range is 10-20
 * (spec §7.1). Under-trained reads amber, in-range green, over-reaching red —
 * the number alone doesn't tell you which side of the range you're on.
 */
export function volumeColor(sets: number): string {
  if (sets >= 10 && sets <= 20) return "var(--green)";
  if (sets > 20) return "var(--red)";
  return "var(--yellow)";
}
