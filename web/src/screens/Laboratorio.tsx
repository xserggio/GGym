import { useEffect, useState } from "react";

import { BodyMap, recoveryColor } from "../components/BodyMap";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Header } from "../components/Header";
import { es } from "../i18n/es";
import { api, type LabOut } from "../lib/api";
import { numEs } from "../lib/format";

interface LaboratorioProps {
  onBack: () => void;
}

const LOAD_COLOR: Record<string, string> = {
  baja: "var(--blue-text)",
  equilibrada: "var(--green-text)",
  alta: "var(--blue-text)",
  excesiva: "var(--red-text)",
};

const LOAD_ORDER = ["baja", "equilibrada", "alta", "excesiva"];

/** A wall of stalled lifts is noise. The rest are counted rather than hidden:
 * a silent cap would read as "only these four", which is not what it means. */
const STALLED_SHOWN = 4;

/** The verdict about today reuses the recovery bands: the same three states,
 * said about the session instead of about a muscle. */
const VERDICT_COLOR: Record<string, string> = {
  listo: "var(--green-text)",
  justo: "var(--yellow)",
  cargado: "var(--red-text)",
};

export function Laboratorio({ onBack }: LaboratorioProps) {
  const [data, setData] = useState<LabOut | null>(null);

  useEffect(() => {
    api.lab().then(setData).catch(() => undefined);
  }, []);

  const muscleName = (key: string) => es.assistant.muscles[key] ?? key;
  const percentByMuscle: Record<string, number> = {};
  for (const item of data?.recovery ?? []) percentByMuscle[item.muscle] = item.percent;
  const worst = data?.recovery?.[0];
  const confidence = data?.confidence;

  return (
    <div className="flex h-full flex-col" style={{ paddingBottom: "var(--safe-bottom)" }}>
      <Header
        title={es.lab.title}
        leading={
          <Button variant="ghost" onClick={onBack} className="mb-1 !min-h-0 !px-3 !py-1.5">
            {es.actions.back}
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-4 pb-6 pt-4">
        {!data ? (
          <div className="font-mono text-xs text-gris">…</div>
        ) : (
          <div className="flex flex-col gap-6">
            {/* How much history all of this rests on, before any of it. */}
            {confidence && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-gris">
                  {es.lab.confidenceLabel}
                </span>
                {[
                  es.lab.sessionsChip(confidence.sessions),
                  ...(confidence.baseline_days > 0
                    ? [es.lab.baselineChip(confidence.baseline_days)]
                    : []),
                ].map((text) => (
                  <span
                    key={text}
                    className="inline-flex items-center gap-1.5 rounded-full border border-line px-2.5 py-1 font-mono text-[11px] text-gris"
                  >
                    <i
                      className="h-1.5 w-1.5 rounded-full"
                      style={{
                        background: confidence.solid
                          ? "var(--green)"
                          : "var(--yellow)",
                      }}
                    />
                    {text}
                  </span>
                ))}
              </div>
            )}

            {data.today && (
              <section>
                <h2 className="font-display text-[21px] leading-tight">
                  {es.lab.todayTitle}
                </h2>
                <p className="mb-2.5 mt-0.5 text-[12.5px] text-gris">
                  {es.lab.todaySub}
                </p>
                <Card className="p-4">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="font-display text-[24px] leading-none">
                      {data.today.day_name}
                    </span>
                    <span
                      className="font-mono text-[12px]"
                      style={{ color: VERDICT_COLOR[data.today.verdict] }}
                    >
                      {es.lab.todayVerdicts[data.today.verdict]}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-col gap-2 border-t border-line pt-3">
                    {data.today.muscles.map((item) => (
                      <div key={item.muscle} className="flex items-center gap-2.5">
                        <span className="w-[88px] shrink-0 text-[14px]">
                          {muscleName(item.muscle)}
                        </span>
                        <span className="h-[7px] flex-1 overflow-hidden rounded-full bg-line">
                          <span
                            className="block h-full rounded-full"
                            style={{
                              width: `${item.percent}%`,
                              background: recoveryColor(item.percent),
                            }}
                          />
                        </span>
                        <b className="w-[76px] shrink-0 whitespace-nowrap text-right font-mono text-[12px] font-normal tabular-nums text-gris">
                          {Math.round(item.percent)} % · {Math.round(item.sets)}
                        </b>
                      </div>
                    ))}
                  </div>
                  <p className="mt-3 text-[12.5px] leading-snug text-gris">
                    {es.lab.todayHints[data.today.verdict]}
                  </p>
                </Card>
              </section>
            )}

            <section>
              <h2 className="font-display text-[21px] leading-tight">
                {es.lab.recoveryTitle}
              </h2>
              <p className="mb-2.5 mt-0.5 text-[12.5px] text-gris">
                {es.lab.recoverySub}
              </p>

              {!data.recovery ? (
                <Card className="p-4 text-[14px] text-gris">{es.lab.empty}</Card>
              ) : (
                <>
                  <Card className="p-4">
                    <div className="flex justify-center gap-1.5">
                      <div>
                        <BodyMap percentByMuscle={percentByMuscle} side="front" width={128} />
                        <p className="mt-1 text-center font-mono text-[9.5px] uppercase tracking-[0.16em] text-gris">
                          {es.lab.front}
                        </p>
                      </div>
                      <div>
                        <BodyMap percentByMuscle={percentByMuscle} side="back" width={128} />
                        <p className="mt-1 text-center font-mono text-[9.5px] uppercase tracking-[0.16em] text-gris">
                          {es.lab.back}
                        </p>
                      </div>
                    </div>

                    {worst && (
                      <div className="mt-3 flex items-baseline justify-between gap-3 border-t border-line pt-3">
                        <span className="text-[14px]">
                          {es.lab.mostLoaded(muscleName(worst.muscle))}
                        </span>
                        <b className="font-mono text-[15px] font-normal tabular-nums">
                          {es.lab.overall(data.overall_percent ?? 100)}
                        </b>
                      </div>
                    )}
                    {worst?.hours_to_fresh != null && (
                      <p className="mt-1 text-[12.5px] text-gris">
                        {es.lab.toFresh(worst.hours_to_fresh)}
                      </p>
                    )}

                    <div className="mt-2.5 flex flex-wrap gap-3.5">
                      {(["cargado", "recuperando", "fresco"] as const).map((band) => (
                        <span key={band} className="text-[12px] text-gris">
                          <i
                            className="mr-1.5 inline-block h-2 w-2 rounded-full align-[1px]"
                            style={{
                              background: recoveryColor(
                                band === "cargado" ? 40 : band === "recuperando" ? 70 : 95,
                              ),
                            }}
                          />
                          {es.lab.bands[band]}
                        </span>
                      ))}
                    </div>
                  </Card>

                  <Card className="mt-2.5 p-4">
                    <div className="flex flex-col gap-2.5">
                      {data.recovery.map((item) => (
                        <div key={item.muscle} className="flex items-center gap-2.5">
                          <span className="w-[88px] shrink-0 text-[14.5px]">
                            {muscleName(item.muscle)}
                          </span>
                          <span className="h-[7px] flex-1 overflow-hidden rounded-full bg-line">
                            <span
                              className="block h-full rounded-full"
                              style={{
                                width: `${item.percent}%`,
                                background: recoveryColor(item.percent),
                              }}
                            />
                          </span>
                          <b className="w-[42px] shrink-0 text-right font-mono text-[13.5px] font-normal tabular-nums text-gris">
                            {Math.round(item.percent)} %
                          </b>
                        </div>
                      ))}
                    </div>
                    <p className="mt-3.5 text-[12px] leading-snug text-gris">
                      {es.lab.estimateNote}
                    </p>
                  </Card>
                </>
              )}
            </section>

            <section>
              <h2 className="font-display text-[21px] leading-tight">
                {es.lab.loadTitle}
              </h2>
              <p className="mb-2.5 mt-0.5 text-[12.5px] text-gris">{es.lab.loadSub}</p>
              <Card className="p-4">
                {!data.load ? (
                  <p className="text-[14px] text-gris">{es.lab.loadPending}</p>
                ) : (
                  <>
                    <div className="font-display text-[44px] leading-none">
                      {numEs(data.load.ratio)}
                      <span className="text-[19px] text-gris"> ×</span>
                    </div>
                    <div className="mt-3.5 flex gap-[3px]">
                      {LOAD_ORDER.map((band) => (
                        <span
                          key={band}
                          className="h-2 flex-1 rounded-[3px]"
                          style={{
                            background:
                              band === data.load?.band
                                ? LOAD_COLOR[band]
                                : "var(--neutral-fill)",
                          }}
                        />
                      ))}
                    </div>
                    <div className="mt-1.5 flex justify-between font-mono text-[10px] uppercase tracking-[0.08em] text-gris">
                      {LOAD_ORDER.map((band) => (
                        <span key={band}>{es.lab.loadBands[band]}</span>
                      ))}
                    </div>
                    <p className="mt-3 text-[12px] leading-snug text-gris">
                      {es.lab.loadDetail(
                        data.load.acute_sets,
                        data.load.chronic_weekly_sets,
                      )}{" "}
                      {es.lab.loadNote}
                    </p>
                  </>
                )}
              </Card>
            </section>

            {data.stalled.length > 0 && (
              <section>
                <h2 className="font-display text-[21px] leading-tight">
                  {es.lab.stalledTitle}
                </h2>
                <p className="mb-2.5 mt-0.5 text-[12.5px] text-gris">
                  {es.lab.stalledSub}
                </p>
                <Card className="p-4">
                  <div className="flex flex-col gap-3">
                    {data.stalled.slice(0, STALLED_SHOWN).map((item) => (
                      <div key={item.exercise_id}>
                        <div className="text-[15px] leading-snug">
                          {item.exercise_name}
                        </div>
                        <div className="font-mono text-[11.5px] text-gris">
                          {es.lab.stalledDetail(item.sessions, item.days_since_best)}
                        </div>
                      </div>
                    ))}
                  </div>
                  {data.stalled.length > STALLED_SHOWN && (
                    <p className="mt-2.5 font-mono text-[11.5px] text-gris">
                      {es.lab.stalledMore(data.stalled.length - STALLED_SHOWN)}
                    </p>
                  )}
                  <p className="mt-3.5 text-[12px] leading-snug text-gris">
                    {es.lab.stalledNote}
                  </p>
                </Card>
              </section>
            )}

            {data.trend && (
              <section>
                <h2 className="font-display text-[21px] leading-tight">
                  {es.lab.trendTitle}
                </h2>
                <p className="mb-2.5 mt-0.5 text-[12.5px] text-gris">
                  {es.lab.trendSub}
                </p>
                <Card className="p-4">
                  <div className="flex flex-col gap-2.5">
                    {data.trend.map((row) => {
                      const top = Math.max(...row.weekly, 1);
                      return (
                        <div key={row.muscle} className="flex items-center gap-2.5">
                          <span className="w-[88px] shrink-0 text-[14px]">
                            {muscleName(row.muscle)}
                          </span>
                          {/* Eight weeks, oldest left. Empty weeks stay as a
                              faint tick: hiding them would flatter the month. */}
                          <span className="flex h-[22px] flex-1 items-end gap-[2px]">
                            {row.weekly.map((value, i) => (
                              <span
                                key={i}
                                className="flex-1 rounded-[1px]"
                                style={{
                                  height: value > 0 ? `${(value / top) * 100}%` : "2px",
                                  minHeight: "2px",
                                  background:
                                    value > 0 ? "var(--ink)" : "var(--neutral-fill)",
                                  opacity: value > 0 ? 0.8 : 1,
                                }}
                              />
                            ))}
                          </span>
                          <span
                            className="w-[52px] shrink-0 text-right font-mono text-[11.5px]"
                            style={{
                              color:
                                row.trend === "sube"
                                  ? "var(--green-text)"
                                  : row.trend === "baja"
                                    ? "var(--red-text)"
                                    : "var(--gris)",
                            }}
                          >
                            {es.lab.trends[row.trend]}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              </section>
            )}

            {confidence && !confidence.solid && data.recovery && (
              <p className="text-[12.5px] leading-snug text-gris">{es.lab.thinNote}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
