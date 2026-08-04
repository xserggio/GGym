/** Spanish decimal comma: 82.5 -> "82,5". */
export function numEs(value: number): string {
  return String(value).replace(".", ",");
}

/** Seconds -> "m:ss". */
export function mmss(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}
