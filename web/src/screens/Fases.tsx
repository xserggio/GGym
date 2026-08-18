import { useEffect, useState } from "react";

import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Header } from "../components/Header";
import { es } from "../i18n/es";
import {
  api,
  type AssessmentOut,
  type PhaseAdviceOut,
  type PhaseKind,
  type PhaseOut,
  type PhasesOut,
} from "../lib/api";
import { dateShortEs, numEs } from "../lib/format";

interface FasesProps {
  onBack: () => void;
}

const KINDS: PhaseKind[] = ["superavit", "definicion", "mantenimiento"];

/** Asked in this order: what you want, where you start, and what your body can
 * take right now. */
const QUESTIONS = [
  "objetivo",
  "grasa",
  "experiencia",
  "dieta_reciente",
  "energia",
  "prioridad",
  "fecha",
] as const;

/** One hue per phase, used only where the colour says which phase this is:
 * growing, cutting, holding. It is a label, not decoration. */
const kindColor: Record<string, string> = {
  superavit: "var(--green)",
  definicion: "var(--blue)",
  mantenimiento: "var(--gris)",
};

/** The same three hues for text and small marks, where dark mode needs them
 * lifted to stay readable. */
const kindInk: Record<string, string> = {
  superavit: "var(--green-text)",
  definicion: "var(--blue-text)",
  mantenimiento: "var(--gris)",
};

/** Green on target; amber otherwise. Never red: being off the intended rate is
 * information to act on, not a failure. */
const verdictColor = (verdict: string) =>
  verdict === "en_rumbo"
    ? "var(--green)"
    : verdict === "sin_datos"
      ? "var(--gris)"
      : "var(--yellow)";

const pct = (value: number) => `${value > 0 ? "+" : ""}${numEs(value)}`;

export function Fases({ onBack }: FasesProps) {
  const [data, setData] = useState<PhasesOut | null>(null);
  const [choosing, setChoosing] = useState(false);
  const [kind, setKind] = useState<PhaseKind>("definicion");
  const [rate, setRate] = useState<number | null>(null);
  const [targetDate, setTargetDate] = useState("");
  const [targetWeight, setTargetWeight] = useState("");
  const [advice, setAdvice] = useState<PhaseAdviceOut | null>(null);
  const [assessing, setAssessing] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [plan, setPlan] = useState<AssessmentOut | null>(null);
  /** Which question is on screen. QUESTIONS.length means "showing the result". */
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);

  /* Only the date check lives here now — which weight fits which date. The
     rate itself comes from the assessment. */
  useEffect(() => {
    if (!data?.enabled || !targetWeight || !targetDate) {
      setAdvice(null);
      return;
    }
    void api
      .phaseAdvice({
        kind,
        target_weight_kg: Number(targetWeight),
        target_date: targetDate,
      })
      .then(setAdvice)
      .catch(() => setAdvice(null));
  }, [data?.enabled, kind, targetWeight, targetDate]);

  useEffect(() => {
    api.phases().then(setData).catch(() => undefined);
  }, []);

  const limitsFor = (k: PhaseKind) => data?.limits.find((l) => l.kind === k);

  const pickKind = (k: PhaseKind) => {
    setKind(k);
    setRate(limitsFor(k)?.default_rate_pct ?? null);
  };

  /** Record an answer and move on. Going back to change one answer returns
   * straight to the result rather than walking the rest again. */
  const answer = (question: string, value: string) => {
    const next = { ...answers, [question]: value };
    setAnswers(next);
    if (QUESTIONS.every((q) => next[q])) {
      void api.phaseAssessment(next).then(setPlan).catch(() => undefined);
      setStep(QUESTIONS.length);
      return;
    }
    const from = QUESTIONS.indexOf(question as (typeof QUESTIONS)[number]);
    const pending = QUESTIONS.findIndex((q, i) => i > from && !next[q]);
    setStep(pending >= 0 ? pending : QUESTIONS.findIndex((q) => !next[q]));
  };

  const run = (action: () => Promise<PhasesOut>) => {
    setBusy(true);
    void action()
      .then((next) => {
        setData(next);
        setChoosing(false);
      })
      .finally(() => setBusy(false));
  };

  const current = data?.current ?? null;
  const limits = limitsFor(kind);
  /** The question on screen, or undefined once the assessment reaches the result. */
  const current_q = step < QUESTIONS.length ? QUESTIONS[step] : undefined;

  const phaseLine = (p: PhaseOut) =>
    `${es.phases.kinds[p.kind]} · ${dateShortEs(p.started_on)}${
      p.ended_on ? ` – ${dateShortEs(p.ended_on)}` : ""
    }`;

  return (
    <div
      className="flex h-full flex-col"
      style={{ paddingBottom: "var(--safe-bottom)" }}
    >
      <Header
        title={es.phases.title}
        leading={
          <Button variant="ghost" onClick={onBack} className="mb-1 !min-h-0 !px-3 !py-1.5">
            {es.actions.back}
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-4 pb-6 pt-4">
        {!data ? (
          <div className="font-mono text-xs text-gris">…</div>
        ) : !data.enabled ? (
          <Card className="p-5 text-sm text-gris">{es.phases.off}</Card>
        ) : assessing ? (
          <div className="flex flex-col gap-5">
            {/* Progress. One segment per question, so the end is visible from
                the first screen and nobody wonders how long this takes. */}
            <div>
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-gris">
                  {step < QUESTIONS.length
                    ? es.phases.assessStep(step + 1, QUESTIONS.length)
                    : es.phases.assessResult}
                </span>
                {step > 0 && step < QUESTIONS.length && (
                  <button
                    type="button"
                    onClick={() => setStep(step - 1)}
                    className="font-mono text-[10px] uppercase tracking-[0.18em] text-gris"
                  >
                    ← {es.phases.assessPrev}
                  </button>
                )}
              </div>
              <div className="mt-2 flex gap-1">
                {QUESTIONS.map((q, i) => (
                  <span
                    key={q}
                    className="h-[3px] flex-1 rounded-full transition-colors"
                    style={{
                      background: answers[q]
                        ? "var(--ink)"
                        : i === step
                          ? "var(--gris)"
                          : "var(--line)",
                    }}
                  />
                ))}
              </div>
            </div>

            {current_q ? (
              (() => {
                const q = current_q;
                return (
                  <section>
                    <h2 className="font-display text-[26px] leading-tight">
                      {es.phases.questions[q]}
                    </h2>
                    {step === 0 && (
                      <p className="mt-2 text-[13px] leading-snug text-gris">
                        {es.phases.assessIntro}
                      </p>
                    )}
                    <div className="mt-4 flex flex-col gap-2">
                      {Object.entries<string>(es.phases.options[q] ?? {}).map(([value, label]) => {
                        const chosen = answers[q] === value;
                        return (
                          <button
                            key={value}
                            type="button"
                            onClick={() => answer(q, value)}
                            className="flex items-center gap-3 rounded-card border px-4 py-3.5 text-left text-[14px] leading-snug transition-colors"
                            style={{
                              borderColor: chosen ? "var(--ink)" : "var(--line)",
                              background: chosen ? "var(--tint)" : "transparent",
                            }}
                          >
                            <span
                              className="grid h-[18px] w-[18px] shrink-0 place-items-center rounded-full border"
                              style={{
                                borderColor: chosen ? "var(--ink)" : "var(--line)",
                                background: chosen ? "var(--ink)" : "transparent",
                              }}
                            >
                              {chosen && (
                                <span
                                  className="h-[6px] w-[6px] rounded-full"
                                  style={{ background: "var(--paper)" }}
                                />
                              )}
                            </span>
                            {label}
                          </button>
                        );
                      })}
                    </div>
                  </section>
                );
              })()
            ) : !plan ? (
              <div className="font-mono text-xs text-gris">…</div>
            ) : (
              <>
                {/* The colour band is the phase: green builds, blue cuts, grey
                    holds. Nothing else on this card is coloured. */}
                <Card className="overflow-hidden">
                  <div
                    className="h-1.5 w-full"
                    style={{ background: kindColor[plan.kind] ?? "var(--gris)" }}
                  />
                  <div className="p-4">
                    <div className="font-display text-[32px] leading-none">
                      {es.phases.kinds[plan.kind]}
                    </div>
                    <div className="mt-1 text-[13px] text-gris">
                      {es.phases.kindHints[plan.kind]}
                    </div>

                    <div className="mt-4 flex gap-6 border-t border-line pt-3">
                      <div>
                        <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                          {es.phases.assessRate}
                        </div>
                        <div
                          className="font-mono text-[19px] tabular-nums"
                          style={{ color: kindInk[plan.kind] ?? "var(--ink)" }}
                        >
                          {plan.rate_pct === 0 ? (
                            <span className="text-[13px] text-gris">
                              {es.phases.assessNoRate}
                            </span>
                          ) : (
                            <>
                              {pct(plan.rate_pct)}
                              <span className="text-[13px] text-gris"> %/sem</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                          {es.phases.assessDuration}
                        </div>
                        <div className="font-mono text-[19px] tabular-nums">
                          {plan.weeks} <span className="text-[13px] text-gris">sem</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>

                <section>
                  {/* A section heading, not a kicker: nothing follows it that
                      carries the weight, so it has to carry it itself. */}
                  <h2 className="mb-2.5 font-display text-[21px] leading-tight">
                    {es.phases.assessWhy}
                  </h2>
                  <ul className="flex flex-col gap-3">
                    {plan.reasons
                      .filter((r) => es.phases.reasons[r])
                      .map((r) => (
                        <li key={r} className="flex gap-3">
                          <span
                            className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full"
                            style={{ background: kindInk[plan.kind] ?? "var(--gris)" }}
                          />
                          <span className="text-[14px] leading-snug">{es.phases.reasons[r]}</span>
                        </li>
                      ))}
                  </ul>
                </section>

                {/* Every answer stays visible and editable: the advice is only
                    as good as what it was told, and she can check that. */}
                <section>
                  <h2 className="mb-2.5 font-display text-[21px] leading-tight">
                    {es.phases.assessAnswers}
                  </h2>
                  <div className="divide-y divide-line rounded-card border border-line">
                    {QUESTIONS.map((q, i) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => setStep(i)}
                        className="flex w-full items-center gap-3 px-3.5 py-2.5 text-left"
                      >
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-[12px] text-gris">
                            {es.phases.questions[q]}
                          </span>
                          <span className="block text-[14px]">
                            {(answers[q] && es.phases.options[q]?.[answers[q]]) || "—"}
                          </span>
                        </span>
                        <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                          {es.phases.assessEdit}
                        </span>
                      </button>
                    ))}
                  </div>
                </section>

                <p className="text-[11px] leading-snug text-gris">
                  {es.phases.assessDisclaimer}
                </p>

                <div className="flex gap-2">
                  <Button
                    variant="primary"
                    className="flex-1"
                    onClick={() => {
                      /* Prefill the form; the user still confirms and can edit
                         every field before anything is saved. */
                      pickKind(plan.kind);
                      setRate(plan.rate_pct);
                      setTargetDate(plan.suggested_target_date);
                      setAssessing(false);
                      setChoosing(true);
                    }}
                  >
                    {es.phases.assessApply}
                  </Button>
                  <button
                    type="button"
                    onClick={() => setAssessing(false)}
                    className="h-touch flex-1 rounded-card border border-line text-sm"
                  >
                    {es.profiles.cancel}
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-5">
            {choosing || !current ? (
              <Card className="p-4">
                <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                  {current ? es.phases.change : es.phases.none}
                </div>

                <div className="mt-3 flex flex-col gap-2">
                  {KINDS.map((k) => {
                    const active = k === kind;
                    return (
                      <button
                        key={k}
                        type="button"
                        onClick={() => pickKind(k)}
                        className="rounded-card border p-3 text-left"
                        style={{
                          borderColor: active ? "var(--ink)" : "var(--line)",
                          background: active ? "var(--tint)" : "transparent",
                        }}
                      >
                        <div className="text-[15px] font-medium">{es.phases.kinds[k]}</div>
                        <div className="mt-0.5 text-[12px] leading-snug text-gris">
                          {es.phases.kindHints[k]}
                        </div>
                      </button>
                    );
                  })}
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setAssessing(true);
                    setAnswers({});
                    setPlan(null);
                    setStep(0);
                  }}
                  className="mt-3 h-touch w-full rounded-card border border-line text-sm text-blue"
                >
                  {es.phases.assessOpen}
                </button>

                {limits && limits.min_rate_pct !== limits.max_rate_pct && (
                  <div className="mt-4">
                    <div className="flex items-baseline justify-between">
                      <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                        {es.phases.rate}
                      </span>
                      <span className="font-mono text-sm tabular-nums">
                        {pct(rate ?? limits.default_rate_pct)} {es.phases.perWeek}
                      </span>
                    </div>
                    {/* The slider cannot leave the guideline range, so an unsafe
                        target is not something the user can pick by accident. */}
                    <input
                      type="range"
                      min={Math.min(limits.min_rate_pct, limits.max_rate_pct)}
                      max={Math.max(limits.min_rate_pct, limits.max_rate_pct)}
                      step={0.05}
                      value={rate ?? limits.default_rate_pct}
                      onChange={(e) => setRate(Number(e.target.value))}
                      className="mt-2 w-full accent-blue"
                    />
                  </div>
                )}

                <label className="mt-4 flex flex-col gap-1">
                  <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                    {es.phases.targetDate}
                  </span>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    className="h-touch rounded-field border border-line bg-paper px-3 font-mono text-sm text-ink"
                  />
                </label>

                <label className="mt-3 flex flex-col gap-1">
                  <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                    {es.phases.targetWeight}
                  </span>
                  <input
                    type="number"
                    inputMode="decimal"
                    step="0.1"
                    value={targetWeight}
                    onChange={(e) => setTargetWeight(e.target.value)}
                    className="h-touch rounded-field border border-line bg-paper px-3 font-mono text-sm text-ink"
                  />
                </label>

                {advice?.feasibility && (
                  <div
                    className="mt-3 rounded-card px-3 py-2.5 text-[13px] leading-snug"
                    style={{
                      background:
                        advice.feasibility.verdict === "viable"
                          ? "rgba(46,139,87,0.12)"
                          : "rgba(242,194,48,0.12)",
                    }}
                  >
                    {advice.feasibility.verdict === "viable"
                      ? es.phases.feasible(advice.feasibility.weeks)
                      : advice.feasibility.verdict === "direccion_contraria"
                        ? es.phases.wrongDirection
                        : es.phases.tooDemanding(
                            numEs(advice.feasibility.required_rate_pct),
                            numEs(advice.feasibility.safe_rate_pct),
                            numEs(advice.feasibility.reachable_weight_kg ?? 0),
                            Math.ceil(advice.feasibility.weeks_needed ?? 0),
                          )}
                  </div>
                )}
                {targetWeight && targetDate && advice && !advice.current_weight_kg && (
                  <p className="mt-2 text-[12px] leading-snug text-gris">
                    {es.phases.needWeight}
                  </p>
                )}

                <div className="mt-4 flex gap-2">
                  <Button
                    variant="primary"
                    disabled={busy}
                    className="flex-1"
                    onClick={() =>
                      run(() =>
                        api.startPhase({
                          kind,
                          target_rate_pct: rate,
                          target_date: targetDate || null,
                          target_weight_kg: targetWeight ? Number(targetWeight) : null,
                        }),
                      )
                    }
                  >
                    {es.phases.start}
                  </Button>
                  {current && (
                    <button
                      type="button"
                      onClick={() => setChoosing(false)}
                      className="h-touch flex-1 rounded-card border border-line text-sm"
                    >
                      {es.profiles.cancel}
                    </button>
                  )}
                </div>
              </Card>
            ) : (
              <Card className="p-4">
                <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                  {es.phases.kinds[current.kind]}
                </div>
                <div className="mt-1 font-display text-[30px] leading-none">
                  {es.phases.week(current.status?.weeks_elapsed ?? 0)}
                </div>

                <div className="mt-3 flex items-baseline gap-4">
                  <div>
                    <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                      {es.phases.target}
                    </div>
                    <div className="font-mono text-sm tabular-nums">
                      {pct(current.target_rate_pct)} {es.phases.perWeek}
                    </div>
                  </div>
                  <div>
                    <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                      {es.phases.actual}
                    </div>
                    <div
                      className="font-mono text-sm tabular-nums"
                      style={{ color: verdictColor(current.status?.verdict ?? "sin_datos") }}
                    >
                      {current.status?.actual_rate_pct != null
                        ? `${pct(current.status.actual_rate_pct)} ${es.phases.perWeek}`
                        : "—"}
                    </div>
                  </div>
                </div>

                {current.status && (
                  <>
                    <p
                      className="mt-3 text-[14px] leading-snug"
                      style={{ color: verdictColor(current.status.verdict) }}
                    >
                      {es.phases.verdicts[current.status.verdict]}
                    </p>
                    {es.phases.verdictHints[current.status.verdict] && (
                      <p className="mt-1 text-[12px] leading-snug text-gris">
                        {es.phases.verdictHints[current.status.verdict]}
                      </p>
                    )}
                    {current.status.duration !== "ok" && (
                      <p className="mt-3 rounded-card px-3 py-2.5 text-[13px] leading-snug text-ink"
                        style={{ background: "rgba(242,194,48,0.12)" }}
                      >
                        {es.phases.duration[current.status.duration]}
                      </p>
                    )}
                    {current.status.days_to_target != null &&
                      current.status.days_to_target > 0 && (
                        <p className="mt-2 font-mono text-[11px] text-gris">
                          {es.phases.daysToTarget(current.status.days_to_target)}
                        </p>
                      )}
                    {current.kind === "definicion" && (
                      <p className="mt-3 text-[12px] leading-snug text-gris">
                        {es.phases.holdingLoad}
                      </p>
                    )}
                  </>
                )}

                <div className="mt-4 flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      pickKind(current.kind);
                      setChoosing(true);
                    }}
                    className="h-touch flex-1 rounded-card border border-line text-sm"
                  >
                    {es.phases.change}
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => run(() => api.endPhase())}
                    className="h-touch flex-1 rounded-card border border-line text-sm"
                  >
                    {es.phases.end}
                  </button>
                </div>
              </Card>
            )}

            <section>
              <div className="mb-2 font-mono text-[9px] uppercase tracking-[0.18em] text-gris">
                {es.phases.history}
              </div>
              <Card className="p-4">
                {data.history.length === 0 ? (
                  <p className="text-sm text-gris">{es.phases.noHistory}</p>
                ) : (
                  <div className="flex flex-col">
                    {data.history.map((p) => (
                      <div
                        key={p.id}
                        className="flex items-baseline justify-between gap-3 border-t border-line py-2.5 first:border-t-0 first:pt-0"
                      >
                        <span className="text-[13px]">{phaseLine(p)}</span>
                        <span className="font-mono text-[11px] tabular-nums text-gris">
                          {pct(p.target_rate_pct)} {es.phases.perWeek}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
