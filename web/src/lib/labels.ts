import { es } from "../i18n/es";

/**
 * Backend enums (movement pattern, equipment) are snake_case ids. Screens must
 * render these labels, never the raw value — falling back to a de-underscored
 * form so a value added server-side degrades readably instead of leaking "an id".
 */
const humanize = (value: string) => value.replace(/_/g, " ");

export const patternLabel = (pattern: string): string =>
  es.patterns[pattern] ?? humanize(pattern);

export const equipmentLabel = (equipment: string): string =>
  es.equipment[equipment] ?? humanize(equipment);
