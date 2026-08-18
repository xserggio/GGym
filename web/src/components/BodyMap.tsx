import {
  BACK_POLYGONS,
  FRONT_POLYGONS,
  VIEWBOX,
  type BodyPolygon,
} from "./bodyPolygons";

/**
 * The body, front and back, with each muscle filled by how recovered it is.
 *
 * Earlier versions built the figure from rounded rectangles and ellipses laid
 * over a grey body, and it always read as stickers on a mannequin — because the
 * muscles were sitting *on* the body instead of being it. These are anatomical
 * regions that tile into the silhouette: what is not a muscle (head, forearms,
 * knees) is drawn in the neutral fill, and the outline is whatever the regions
 * add up to.
 */

/** Same three bands as the recovery service, so the colours agree with the
 * words printed next to them. */
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

export function BodyMap({ percentByMuscle, side, width = 150 }: BodyMapProps) {
  const polygons: BodyPolygon[] =
    side === "front" ? FRONT_POLYGONS : BACK_POLYGONS;
  return (
    <svg
      viewBox={VIEWBOX}
      width={width}
      height={width * 2}
      aria-hidden
      style={{ display: "block" }}
    >
      {/* A hairline in the card colour separates neighbouring regions; without
          it two muscles in the same state merge into one shapeless mass. */}
      <g stroke="var(--paper)" strokeWidth="0.4" strokeLinejoin="round">
        {polygons.map((polygon, i) => (
          <polygon
            key={i}
            points={polygon.p}
            fill={
              polygon.m
                ? recoveryColor(percentByMuscle[polygon.m] ?? 100)
                : "var(--neutral-fill)"
            }
          />
        ))}
      </g>
    </svg>
  );
}
