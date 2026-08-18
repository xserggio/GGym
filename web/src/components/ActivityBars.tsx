import type { ActivityPoint } from "../lib/api";

interface ActivityBarsProps {
  points: ActivityPoint[];
  accent: string;
}

/**
 * Work per day (or per month over long windows). Trained buckets are drawn in
 * the accent colour at a height proportional to the volume lifted; rest days
 * keep a faint baseline tick so the gaps stay visible — the pattern of misses
 * is the useful signal, and a chart that skipped them would flatter the user.
 */
export function ActivityBars({ points, accent }: ActivityBarsProps) {
  if (points.length === 0) return null;
  const max = Math.max(...points.map((p) => p.volume_kg), 1);

  return (
    <div className="flex h-10 items-end gap-[3px]" aria-hidden>
      {points.map((p) => {
        const trained = p.sessions > 0;
        return (
          <span
            key={p.bucket}
            className="flex-1 rounded-[1px]"
            style={{
              height: trained ? `${Math.max(18, (p.volume_kg / max) * 100)}%` : "2px",
              background: trained ? accent : "var(--line)",
            }}
          />
        );
      })}
    </div>
  );
}
