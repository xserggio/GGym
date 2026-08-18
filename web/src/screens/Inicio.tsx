import { useEffect, useState } from "react";

import { ActivityBars } from "../components/ActivityBars";
import { BarbellChart } from "../components/BarbellChart";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Header } from "../components/Header";
import { Logo } from "../components/Logo";
import { PeriodTabs, type Period } from "../components/PeriodTabs";
import { es } from "../i18n/es";
import { api, type HomeOut } from "../lib/api";
import { dateShortEs, numEs } from "../lib/format";
import { patternLabel } from "../lib/labels";
import { sessionColor, volumeColor } from "../lib/palette";

interface InicioProps {
  onStart: () => void;
  onTreadmill: () => void;
  onWeight: () => void;
  onSettings: () => void;
}

/**
 * A measured figure on its own surface. Hierarchy comes from size — `hero`
 * spans the grid and sets the screen's focal point — never from colour, so the
 * tiles read as a considered set instead of a row of identical boxes.
 */
/**
 * Change against the same window immediately before. Green up, amber down:
 * the only honest judgement available is "more or less work than your own
 * recent form" — no invented target, no streak. Hidden when there is nothing
 * to compare against (all-time, or a first period).
 */
function Delta({ current, previous }: { current: number; previous: number | null }) {
  // Nothing to compare against: no previous window, or it was empty. A change
  // from zero is not a percentage, and the raw difference is in base units
  // (seconds, kilos) that would read as a nonsense number next to the value.
  if (previous === null || previous <= 0) return null;
  const diff = current - previous;
  const pct = Math.round((diff / previous) * 100);
  if (pct === 0) return null;
  return (
    <span
      className="font-mono text-[10px]"
      style={{ color: pct > 0 ? "var(--green)" : "var(--yellow)" }}
      title={es.home.vsPrev}
    >
      {pct > 0 ? "▲" : "▼"} {Math.abs(pct)}%
    </span>
  );
}

function Stat({
  label,
  value,
  unit,
  note,
  hero,
  onClick,
  delta,
}: {
  label: string;
  value: string;
  unit?: string;
  note?: string;
  hero?: boolean;
  onClick?: () => void;
  delta?: React.ReactNode;
}) {
  return (
    <Card
      className={`${hero ? "col-span-2 p-4" : "p-3"} ${onClick ? "text-left" : ""}`}
      {...(onClick ? { role: "button", onClick } : {})}
    >
      <div className="flex items-baseline gap-1.5">
        <span className="min-w-0 flex-1 truncate font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
          {label}
        </span>
        {onClick && <span className="font-mono text-[10px] text-blue">›</span>}
      </div>
      <div className="mt-1.5 flex items-baseline gap-1">
        <span
          className={`font-display leading-none tabular-nums ${
            hero ? "text-[52px]" : "text-[30px]"
          }`}
        >
          {value}
        </span>
        {unit && <span className="font-mono text-[11px] text-gris">{unit}</span>}
        {delta && <span className="ml-auto">{delta}</span>}
      </div>
      {note && <div className="mt-1 font-mono text-[10px] text-gris">{note}</div>}
    </Card>
  );
}

/** Small caps rule that opens a zone. */
function ZoneLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-2 font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
      {children}
    </div>
  );
}

const hoursMinutes = (seconds: number) => {
  const total = Math.round(seconds / 60);
  const h = Math.floor(total / 60);
  return h > 0 ? `${h} h ${String(total % 60).padStart(2, "0")}` : `${total}`;
};

export function Inicio({ onStart, onTreadmill, onWeight, onSettings }: InicioProps) {
  const [home, setHome] = useState<HomeOut | null>(null);
  const [period, setPeriod] = useState<Period>("7d");

  useEffect(() => {
    api.home(period).then(setHome).catch(() => undefined);
  }, [period]);

  const maxSets = Math.max(1, ...(home?.volume ?? []).map((g) => g.sets));
  const heavy = home ? home.week_volume_kg >= 1000 : false;
  // Everything tied to "the session you are about to do" shares its colour.
  const accent = sessionColor(home?.next_position ?? 1);
  const nothingLogged =
    home !== null &&
    home.volume.length === 0 &&
    home.milestones.length === 0 &&
    home.records.length === 0;

  return (
    <div className="flex h-full flex-col">
      <Header
        brand={<Logo />}
        action={
          <Button variant="ghost" onClick={onSettings} className="!min-h-0 !px-3 !py-1.5">
            {es.actions.settings}
          </Button>
        }
      />

      {!home ? (
        <div className="flex flex-1 items-center justify-center font-mono text-xs text-gris">
          …
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4 pb-6 pt-4">
          <div className="flex flex-col gap-6">
            {/* What to do now, before what you did. The session number carries
                its wheel colour, the same one the indicator shows in Hoy. */}
            <Card className="p-4">
              <ZoneLabel>{es.home.nextUp}</ZoneLabel>
              <div className="flex items-center gap-2.5">
                <span
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-chip font-mono text-[15px]"
                  style={{ background: accent, color: "var(--paper)" }}
                >
                  {home.next_position}
                </span>
                <div className="min-w-0">
                  <div className="truncate font-display text-[26px] leading-tight">
                    {home.next_day_name}
                  </div>
                  <div className="text-[13px] text-gris">
                    {home.next_exercises} {es.today.exercises} ·{" "}
                    {home.last_session_at
                      ? es.home.lastSession(dateShortEs(home.last_session_at))
                      : es.home.neverTrained}
                  </div>
                </div>
              </div>
              <Button variant="primary" onClick={onStart} className="mt-3 w-full">
                {es.home.start}
              </Button>
            </Card>

            <section>
              <div className="mb-2 flex items-baseline justify-between gap-3">
                <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                  {es.home.week}
                </span>
                <PeriodTabs value={period} onChange={setPeriod} />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Card className="col-span-2 p-4">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                      {es.home.sessions}
                    </span>
                    <span className="flex items-baseline gap-2 font-mono text-[10px] text-gris">
                      <span>
                        {home.week_sets} {es.home.sets} ·{" "}
                        {hoursMinutes(home.week_strength_seconds)}
                        {home.week_strength_seconds >= 3600 ? "" : " min"}
                      </span>
                      <Delta current={home.week_sessions} previous={home.prev_sessions} />
                    </span>
                  </div>
                  <div className="mt-1 font-display text-[52px] leading-none tabular-nums">
                    {home.week_sessions}
                  </div>
                  {/* The rhythm of training against rest, which no single
                      figure can show. Full width: it is a chart, not a badge. */}
                  <div className="mt-3">
                    <ActivityBars points={home.activity} accent={accent} />
                  </div>
                </Card>
                <Stat
                  label={es.home.volume}
                  value={
                    heavy
                      ? numEs(Math.round(home.week_volume_kg / 100) / 10)
                      : numEs(Math.round(home.week_volume_kg))
                  }
                  unit={heavy ? "t" : "kg"}
                  delta={
                    <Delta current={home.week_volume_kg} previous={home.prev_volume_kg} />
                  }
                />
                <Stat
                  label={es.home.kcal}
                  value={home.week_kcal !== null ? `${home.week_kcal}` : "—"}
                  unit={home.week_kcal !== null ? "kcal" : undefined}
                  note={home.week_kcal === null ? es.home.kcalHint : undefined}
                />
                <Stat
                  label={es.home.treadmill}
                  value={hoursMinutes(home.week_treadmill_seconds)}
                  unit={home.week_treadmill_seconds >= 3600 ? undefined : "min"}
                  onClick={onTreadmill}
                  delta={
                    <Delta
                      current={home.week_treadmill_seconds}
                      previous={home.prev_treadmill_seconds}
                    />
                  }
                />
                <Stat
                  label={es.home.bodyweight}
                  value={home.bodyweight_avg7 !== null ? numEs(home.bodyweight_avg7) : "—"}
                  unit={home.bodyweight_avg7 !== null ? "kg" : undefined}
                  note={
                    home.bodyweight_delta_week !== null
                      ? `${home.bodyweight_delta_week > 0 ? "+" : ""}${numEs(
                          home.bodyweight_delta_week,
                        )} ${es.today.vsPrevious}`
                      : es.home.trend
                  }
                  onClick={onWeight}
                />
              </div>
            </section>

            {nothingLogged ? (
              /* Three empty boxes stacked read as a broken screen. One block
                 that says what will appear, and when, reads as a new account. */
              <Card className="p-5">
                <div
                  className="font-mono text-[9px] uppercase tracking-[0.18em]"
                  style={{ color: accent }}
                >
                  {es.home.firstTime}
                </div>
                <p className="mt-2 text-[13px] leading-relaxed text-gris">
                  {es.home.firstTimeHint}
                </p>
              </Card>
            ) : (
              <>
            {/* Balance is the one place colour states what the number cannot:
                whether the volume sits inside the useful range. */}
            <section>
              <ZoneLabel>{es.home.balance}</ZoneLabel>
              <Card className="p-4">
                {home.volume.length === 0 ? (
                  <p className="text-sm text-gris">{es.history.empty}</p>
                ) : (
                  <>
                    <div className="flex flex-col gap-2">
                      {home.volume.map((g) => (
                        <div key={g.pattern} className="flex items-center gap-2">
                          <span className="w-28 shrink-0 truncate text-[13px]">
                            {patternLabel(g.pattern)}
                          </span>
                          <div className="h-2 flex-1 rounded-full bg-line">
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${(g.sets / maxSets) * 100}%`,
                                background: volumeColor(g.sets),
                              }}
                            />
                          </div>
                          <span className="w-6 text-right font-mono text-[11px] tabular-nums text-gris">
                            {g.sets}
                          </span>
                        </div>
                      ))}
                    </div>
                    <p className="mt-3 text-[12px] leading-snug text-gris">
                      {es.home.balanceHint}
                    </p>
                  </>
                )}
              </Card>
            </section>

            <section>
              <ZoneLabel>{es.milestones.title}</ZoneLabel>
              <Card className="p-4">
                {home.milestones.length === 0 ? (
                  <p className="text-sm text-gris">{es.milestones.empty}</p>
                ) : (
                  <div className="flex flex-col">
                    {home.milestones.map((m) => (
                      <div
                        key={m.kind}
                        className="flex items-baseline justify-between gap-3 border-t border-line py-2.5 first:border-t-0 first:pt-0"
                      >
                        <div className="min-w-0">
                          <div className="truncate text-[13px]">
                            {es.milestones[m.kind] ?? m.kind}
                          </div>
                          {(m.detail || m.achieved_on) && (
                            <div className="mt-0.5 truncate font-mono text-[10px] text-gris">
                              {[m.detail, m.achieved_on ? dateShortEs(m.achieved_on) : null]
                                .filter(Boolean)
                                .join(" · ")}
                            </div>
                          )}
                        </div>
                        <div className="flex items-baseline gap-1 whitespace-nowrap">
                          <span className="font-display text-[22px] leading-none tabular-nums">
                            {numEs(m.value)}
                          </span>
                          <span className="font-mono text-[10px] text-gris">{m.unit}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </section>

            <section>
              <ZoneLabel>{es.home.records}</ZoneLabel>
              <Card className="p-4">
                {home.records.length === 0 ? (
                  <p className="text-sm text-gris">{es.home.noRecords}</p>
                ) : (
                  <div className="flex flex-col">
                    {home.records.map((r) => (
                      <div
                        key={r.exercise_id}
                        className="flex items-center gap-3 border-t border-line py-2.5 first:border-t-0 first:pt-0"
                      >
                        <span className="min-w-0 flex-1 truncate text-[13px]">
                          {r.exercise_name}
                        </span>
                        {/* The plates are the colour here: they are the weight. */}
                        <BarbellChart weightKg={r.weight_kg} compact />
                        <span className="font-mono text-sm tabular-nums">
                          {numEs(r.weight_kg)} × {r.reps}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </section>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
