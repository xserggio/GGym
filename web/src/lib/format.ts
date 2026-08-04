/** Spanish decimal comma: 82.5 -> "82,5". */
export function numEs(value: number): string {
  return String(value).replace(".", ",");
}

/** Seconds -> "m:ss". */
export function mmss(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

const MONTHS_ES = [
  "ene", "feb", "mar", "abr", "may", "jun",
  "jul", "ago", "sep", "oct", "nov", "dic",
];

/** ISO date/datetime -> "4 ago". */
export function dateShortEs(iso: string): string {
  const d = new Date(iso);
  return `${d.getDate()} ${MONTHS_ES[d.getMonth()]}`;
}

/** Whole minutes between two ISO timestamps -> "48 min". */
export function durationMin(startIso: string, endIso: string): number {
  return Math.max(0, Math.round((Date.parse(endIso) - Date.parse(startIso)) / 60000));
}
