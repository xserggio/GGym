/**
 * The body, front and back, with each muscle filled by how recovered it is.
 *
 * Two layers: a neutral silhouette whose parts overlap into one figure, and the
 * muscles painted on top of it. Drawing only the muscles leaves a pile of
 * floating blocks that reads as a robot rather than a person — the grey layer
 * is what makes it a body.
 *
 * Built from ellipses and rounded rectangles rather than traced anatomy. At the
 * size a phone gives it, a schematic reads and detail turns to mush.
 */

type Part =
  | { t: "e"; x: number; y: number; rx: number; ry: number; m?: string }
  | { t: "r"; x: number; y: number; w: number; h: number; r: number; m?: string };

const BODY: Part[] = [
  { t: "e", x: 60, y: 21, rx: 12, ry: 14 },
  { t: "r", x: 54, y: 31, w: 12, h: 14, r: 5 },
  { t: "r", x: 38, y: 43, w: 44, h: 46, r: 13 },
  { t: "r", x: 43, y: 78, w: 34, h: 32, r: 9 },
  { t: "r", x: 42, y: 100, w: 36, h: 20, r: 8 },
  { t: "e", x: 38, y: 52, rx: 13, ry: 12 },
  { t: "e", x: 82, y: 52, rx: 13, ry: 12 },
  { t: "r", x: 23, y: 55, w: 14, h: 44, r: 7 },
  { t: "r", x: 83, y: 55, w: 14, h: 44, r: 7 },
  { t: "r", x: 22, y: 93, w: 12.5, h: 40, r: 6 },
  { t: "r", x: 85.5, y: 93, w: 12.5, h: 40, r: 6 },
  { t: "e", x: 28, y: 137, rx: 6, ry: 8 },
  { t: "e", x: 92, y: 137, rx: 6, ry: 8 },
  { t: "r", x: 41, y: 113, w: 18, h: 60, r: 9 },
  { t: "r", x: 61, y: 113, w: 18, h: 60, r: 9 },
  { t: "r", x: 43, y: 165, w: 15, h: 58, r: 7 },
  { t: "r", x: 62, y: 165, w: 15, h: 58, r: 7 },
  { t: "r", x: 41, y: 219, w: 17, h: 10, r: 4 },
  { t: "r", x: 62, y: 219, w: 17, h: 10, r: 4 },
];

const FRONT: Part[] = [
  { t: "e", x: 38, y: 52, rx: 11, ry: 10, m: "hombro" },
  { t: "e", x: 82, y: 52, rx: 11, ry: 10, m: "hombro" },
  { t: "r", x: 43, y: 51, w: 16, h: 20, r: 5, m: "pecho" },
  { t: "r", x: 61, y: 51, w: 16, h: 20, r: 5, m: "pecho" },
  { t: "e", x: 30, y: 74, rx: 6.5, ry: 14, m: "biceps" },
  { t: "e", x: 90, y: 74, rx: 6.5, ry: 14, m: "biceps" },
  { t: "r", x: 50, y: 73, w: 20, h: 30, r: 7, m: "core" },
  { t: "e", x: 50, y: 141, rx: 8, ry: 24, m: "cuadriceps" },
  { t: "e", x: 70, y: 141, rx: 8, ry: 24, m: "cuadriceps" },
];

const BACK: Part[] = [
  { t: "e", x: 38, y: 52, rx: 11, ry: 10, m: "hombro" },
  { t: "e", x: 82, y: 52, rx: 11, ry: 10, m: "hombro" },
  { t: "r", x: 46, y: 49, w: 28, h: 22, r: 7, m: "espalda" },
  { t: "r", x: 44, y: 68, w: 32, h: 25, r: 8, m: "espalda" },
  { t: "e", x: 30, y: 74, rx: 6.5, ry: 14, m: "triceps" },
  { t: "e", x: 90, y: 74, rx: 6.5, ry: 14, m: "triceps" },
  { t: "r", x: 49, y: 92, w: 22, h: 13, r: 5, m: "core" },
  { t: "e", x: 51, y: 116, rx: 11, ry: 11, m: "gluteo" },
  { t: "e", x: 69, y: 116, rx: 11, ry: 11, m: "gluteo" },
  { t: "e", x: 50, y: 148, rx: 8, ry: 22, m: "isquios" },
  { t: "e", x: 70, y: 148, rx: 8, ry: 22, m: "isquios" },
  { t: "e", x: 51, y: 190, rx: 6.5, ry: 17, m: "gemelo" },
  { t: "e", x: 69, y: 190, rx: 6.5, ry: 17, m: "gemelo" },
];

/** Same three bands as the recovery service, so the colours agree with the
 * words the screen prints next to them. */
export function recoveryColor(percent: number): string {
  if (percent < 60) return "var(--red)";
  if (percent < 86) return "var(--yellow)";
  return "var(--green)";
}

interface BodyMapProps {
  /** Percent recovered, keyed by the service's muscle ids. */
  percentByMuscle: Record<string, number>;
  side: "front" | "back";
  width?: number;
}

function shape(part: Part, key: number, fill: string, stroke?: string) {
  const common = {
    key,
    fill,
    ...(stroke ? { stroke, strokeWidth: 1.3 } : {}),
  };
  return part.t === "e" ? (
    <ellipse cx={part.x} cy={part.y} rx={part.rx} ry={part.ry} {...common} />
  ) : (
    <rect
      x={part.x}
      y={part.y}
      width={part.w}
      height={part.h}
      rx={part.r}
      {...common}
    />
  );
}

export function BodyMap({ percentByMuscle, side, width = 150 }: BodyMapProps) {
  const muscles = side === "front" ? FRONT : BACK;
  return (
    <svg
      viewBox="0 0 120 240"
      width={width}
      height={(width * 240) / 120}
      aria-hidden
      style={{ display: "block" }}
    >
      {BODY.map((part, i) => shape(part, i, "var(--neutral-fill)"))}
      {/* The hairline in the card colour keeps two adjacent muscles in the same
          state from merging into one shapeless blob. */}
      {muscles.map((part, i) =>
        shape(
          part,
          100 + i,
          recoveryColor(percentByMuscle[part.m ?? ""] ?? 100),
          "var(--paper)",
        ),
      )}
    </svg>
  );
}
