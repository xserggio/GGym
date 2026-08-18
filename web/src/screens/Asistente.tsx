import { useState } from "react";

import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Header } from "../components/Header";
import { SwapCompare } from "../components/SwapCompare";
import { es } from "../i18n/es";
import {
  api,
  type ChangeOut,
  type FindingOut,
  type RoutineReviewIn,
  type RoutineReviewOut,
} from "../lib/api";

interface AsistenteProps {
  onBack: () => void;
  /** Called after anything is written, so the routine screen reloads. */
  onChanged: () => void;
}

/** Asked in this order: the shape of the week, then the time, then intent, then
 * the two that change what is safe to propose. */
const QUESTIONS = ["dias", "tiempo", "objetivo", "prioridad", "evitar"] as const;
type Question = (typeof QUESTIONS)[number];

/** Only `prioridad` takes several answers — the rest are exclusive. */
const MULTI: Question = "prioridad";

/** Severity is the one thing here that earns colour: it is what tells you what
 * to read first. Bands reuse the same three, so "bajo" and "importante" look
 * alike on purpose. */
const SEVERITY_COLOR: Record<string, string> = {
  importante: "var(--red-text)",
  mejorable: "var(--blue-text)",
  detalle: "var(--gris)",
};

const BAND_COLOR: Record<string, string> = {
  bajo: "var(--red-text)",
  justo: "var(--blue-text)",
  efectivo: "var(--green-text)",
  alto: "var(--blue-text)",
};

type Detail = Record<string, string>;

const say = (
  table: Record<string, (d: Detail) => string>,
  finding: FindingOut,
): string => {
  const fn = table[finding.kind];
  if (!fn) return "";
  // The service speaks in muscle keys; the sentences must not. Left raw, a
  // finding would tell her about her "gluteo" and her "core".
  const detail = { ...((finding.detail ?? {}) as Detail) };
  if (detail.muscle) {
    detail.muscle = es.assistant.muscles[detail.muscle] ?? detail.muscle;
  }
  return fn(detail);
};

export function Asistente({ onBack, onChanged }: AsistenteProps) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [review, setReview] = useState<RoutineReviewOut | null>(null);
  const [accepted, setAccepted] = useState<Set<string>>(new Set());
  const [changes, setChanges] = useState<ChangeOut[] | null>(null);
  /** The swap being inspected side by side, if any. */
  const [comparing, setComparing] = useState<FindingOut | null>(null);
  /** What finished, and the profile name to point at. The two paths leave the
   * user in different places, so they must not share a sentence: one saved a
   * backup, the other switched her to a new routine entirely. */
  const [done, setDone] = useState<
    { kind: "edits" | "restructure"; name: string } | null
  >(null);
  const [busy, setBusy] = useState(false);

  const body = (): RoutineReviewIn => ({
    dias: Number(answers.dias ?? 4),
    tiempo: String(answers.tiempo ?? "60"),
    objetivo: String(answers.objetivo ?? "equilibrio"),
    evitar: String(answers.evitar ?? "nada"),
    prioridad: (answers.prioridad as string[] | undefined) ?? [],
  });

  const runReview = (next: Record<string, string | string[]>) => {
    setBusy(true);
    const payload: RoutineReviewIn = {
      dias: Number(next.dias ?? 4),
      tiempo: String(next.tiempo ?? "60"),
      objetivo: String(next.objetivo ?? "equilibrio"),
      evitar: String(next.evitar ?? "nada"),
      prioridad: (next.prioridad as string[] | undefined) ?? [],
    };
    void api
      .routineReview(payload)
      .then((result) => {
        setReview(result);
        // Pre-tick what matters; the details stay for her to opt into.
        setAccepted(
          new Set(
            result.findings
              .filter((f) => f.action_kind && f.severity === "importante")
              .map((f) => f.id),
          ),
        );
      })
      .finally(() => setBusy(false));
  };

  const answer = (question: Question, value: string) => {
    if (question === MULTI) {
      const current = new Set((answers[question] as string[]) ?? []);
      if (value === "nada") current.clear();
      else if (current.has(value)) current.delete(value);
      else current.add(value);
      setAnswers({ ...answers, [question]: [...current] });
      return; // multi-select waits for the explicit continue
    }
    const next = { ...answers, [question]: value };
    setAnswers(next);
    const pending = QUESTIONS.findIndex((q, i) => i > step && !next[q]);
    if (pending >= 0) setStep(pending);
    else {
      setStep(QUESTIONS.length);
      runReview(next);
    }
  };

  const advance = () => {
    const next: Record<string, string | string[]> = {
      ...answers,
      prioridad: (answers.prioridad as string[] | undefined) ?? [],
    };
    setAnswers(next);
    const pending = QUESTIONS.findIndex((q, i) => i > step && !next[q]);
    if (pending >= 0) setStep(pending);
    else {
      setStep(QUESTIONS.length);
      runReview(next);
    }
  };

  const toggle = (id: string) => {
    const next = new Set(accepted);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setAccepted(next);
  };

  const goReview = () => {
    setBusy(true);
    void api
      .routinePreview(body(), [...accepted])
      .then(setChanges)
      .finally(() => setBusy(false));
  };

  const confirm = () => {
    setBusy(true);
    void api
      .routineApply(body(), [...accepted])
      .then((result) => {
        setDone({ kind: "edits", name: result.snapshot ?? "" });
        onChanged();
      })
      .finally(() => setBusy(false));
  };

  const applyRestructure = () => {
    setBusy(true);
    void api
      .routineRestructure(body())
      .then((result) => {
        setDone({ kind: "restructure", name: result.snapshot ?? "" });
        onChanged();
      })
      .finally(() => setBusy(false));
  };

  const current = step < QUESTIONS.length ? QUESTIONS[step] : undefined;
  const actionable = review?.findings.filter((f) => f.action_kind) ?? [];

  return (
    <div className="flex h-full flex-col" style={{ paddingBottom: "var(--safe-bottom)" }}>
      <Header
        title={es.assistant.title}
        leading={
          <Button variant="ghost" onClick={onBack} className="mb-1 !min-h-0 !px-3 !py-1.5">
            {es.actions.back}
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-4 pb-6 pt-4">
        {done ? (
          <Card className="p-5">
            <div className="font-display text-[26px] leading-tight">
              {done.kind === "restructure"
                ? es.assistant.restructureDone
                : es.assistant.applied(accepted.size)}
            </div>
            <p className="mt-2 text-[13px] leading-snug text-gris">
              {done.kind === "restructure"
                ? es.assistant.restructureDoneHint(done.name)
                : es.assistant.undoHint(done.name)}
            </p>
            <Button variant="primary" className="mt-4 w-full" onClick={onBack}>
              {es.actions.back}
            </Button>
          </Card>
        ) : changes ? (
          /* Step three: exactly what will change, before it does. */
          <div className="flex flex-col gap-4">
            <h2 className="font-display text-[26px] leading-tight">
              {es.assistant.reviewTitle}
            </h2>
            <div className="divide-y divide-line rounded-card border border-line">
              {changes.map((change, i) => (
                <div key={i} className="px-3.5 py-3">
                  <div className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-gris">
                    {es.assistant.changeKinds[change.kind] ?? change.kind} ·{" "}
                    {change.day}
                  </div>
                  <div className="mt-1 text-[15px]">{change.exercise}</div>
                  <div className="mt-1 font-mono text-[13px] tabular-nums">
                    <span className="text-gris line-through">{change.before}</span>
                    <span className="mx-1.5 text-gris">→</span>
                    <span>{change.after}</span>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-[12.5px] leading-snug text-gris">
              {es.assistant.snapshotNote}
            </p>
            <div className="flex gap-2">
              <Button
                variant="primary"
                className="flex-1"
                disabled={busy || changes.length === 0}
                onClick={confirm}
              >
                {es.assistant.applySelected(changes.length)}
              </Button>
              <button
                type="button"
                onClick={() => setChanges(null)}
                className="h-touch flex-1 rounded-card border border-line text-sm"
              >
                {es.profiles.cancel}
              </button>
            </div>
          </div>
        ) : current ? (
          /* Step one: one question at a time. */
          <div className="flex flex-col gap-5">
            <div>
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-gris">
                  {es.assistant.step(step + 1, QUESTIONS.length)}
                </span>
                {step > 0 && (
                  <button
                    type="button"
                    onClick={() => setStep(step - 1)}
                    className="font-mono text-[10px] uppercase tracking-[0.18em] text-gris"
                  >
                    ← {es.assistant.prev}
                  </button>
                )}
              </div>
              <div className="mt-2 flex gap-1">
                {QUESTIONS.map((q, i) => (
                  <span
                    key={q}
                    className="h-[3px] flex-1 rounded-full transition-colors"
                    style={{
                      background:
                        answers[q] !== undefined
                          ? "var(--ink)"
                          : i === step
                            ? "var(--gris)"
                            : "var(--line)",
                    }}
                  />
                ))}
              </div>
            </div>

            <section>
              <h2 className="font-display text-[26px] leading-tight">
                {es.assistant.questions[current]}
              </h2>
              {step === 0 && (
                <p className="mt-2 text-[13px] leading-snug text-gris">
                  {es.assistant.intro}
                </p>
              )}
              {current === MULTI && (
                <p className="mt-2 text-[12px] text-gris">{es.assistant.multiHint}</p>
              )}
              <div className="mt-4 flex flex-col gap-2">
                {Object.entries<string>(es.assistant.options[current] ?? {}).map(
                  ([value, label]) => {
                    const chosen =
                      current === MULTI
                        ? ((answers[current] as string[]) ?? []).includes(value)
                        : answers[current] === value;
                    return (
                      <button
                        key={value}
                        type="button"
                        onClick={() => answer(current, value)}
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
                  },
                )}
              </div>
              {current === MULTI && (
                <Button variant="primary" className="mt-4 w-full" onClick={advance}>
                  {es.actions.continue}
                </Button>
              )}
            </section>
          </div>
        ) : !review ? (
          <div className="font-mono text-xs text-gris">{es.assistant.analysing}</div>
        ) : (
          /* Step two: what it found. */
          <div className="flex flex-col gap-6">
            <section>
              <h2 className="mb-2.5 font-display text-[21px] leading-tight">
                {es.assistant.volumeTitle}
              </h2>
              <Card className="p-4">
                <div className="flex flex-col gap-2">
                  {review.volumes.map((v) => (
                    <div key={v.muscle} className="flex items-center gap-3">
                      <span className="w-[88px] shrink-0 text-[14.5px]">
                        {es.assistant.muscles[v.muscle] ?? v.muscle}
                      </span>
                      <span className="h-[6px] flex-1 overflow-hidden rounded-full bg-line">
                        <span
                          className="block h-full rounded-full"
                          style={{
                            width: `${Math.min(100, (v.weekly_sets / 24) * 100)}%`,
                            background: BAND_COLOR[v.band],
                          }}
                        />
                      </span>
                      <span className="w-[38px] shrink-0 text-right font-mono text-[13.5px] tabular-nums">
                        {v.weekly_sets}
                      </span>
                    </div>
                  ))}
                </div>
                <p className="mt-3.5 text-[12.5px] leading-snug text-gris">
                  {es.assistant.volumeNote}
                </p>
              </Card>
            </section>

            <section>
              <h2 className="mb-2.5 font-display text-[21px] leading-tight">
                {es.assistant.findingsTitle}
              </h2>
              {actionable.length === 0 && review.findings.length === 0 ? (
                <Card className="p-4 text-[14px] text-gris">
                  {es.assistant.noFindings}
                </Card>
              ) : (
                <div className="flex flex-col gap-2">
                  {review.findings.map((f) => {
                    const chosen = accepted.has(f.id);
                    const clickable = Boolean(f.action_kind);
                    const isSwap = f.action_kind === "sustituir";
                    return (
                      <div
                        key={f.id}
                        className="rounded-card border transition-colors"
                        style={{
                          borderColor: chosen ? "var(--ink)" : "var(--line)",
                          background: chosen ? "var(--tint)" : "transparent",
                        }}
                      >
                        <button
                          type="button"
                          disabled={!clickable}
                          onClick={() => clickable && toggle(f.id)}
                          className="flex w-full items-start gap-3 p-3.5 text-left"
                        >
                          {clickable && (
                            <span
                              className="mt-[3px] grid h-[20px] w-[20px] shrink-0 place-items-center rounded-[5px] border"
                              style={{
                                borderColor: chosen ? "var(--ink)" : "var(--line)",
                                background: chosen ? "var(--ink)" : "transparent",
                              }}
                            >
                              {chosen && (
                                <span
                                  className="text-[12px] leading-none"
                                  style={{ color: "var(--paper)" }}
                                >
                                  ✓
                                </span>
                              )}
                            </span>
                          )}
                          <span className="min-w-0 flex-1">
                            <span
                              className="block font-mono text-[10px] uppercase tracking-[0.16em]"
                              style={{ color: SEVERITY_COLOR[f.severity] }}
                            >
                              {es.assistant.severities[f.severity]}
                            </span>
                            <span className="mt-1 block text-[16px] leading-snug">
                              {say(es.assistant.findings, f)}
                            </span>
                            <span className="mt-1.5 block text-[13.5px] leading-snug text-gris">
                              {say(es.assistant.why, f)}
                            </span>
                          </span>
                        </button>
                        {isSwap && (
                          <button
                            type="button"
                            onClick={() => setComparing(f)}
                            className="w-full border-t border-line px-3.5 py-2.5 text-left text-[13px] text-blue"
                          >
                            {es.assistant.compare} ›
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </section>

            {review.restructure && (
              <section>
                <h2 className="mb-2.5 font-display text-[21px] leading-tight">
                  {es.assistant.restructureTitle}
                </h2>
                <Card className="p-4">
                  <p className="text-[14px] leading-snug text-gris">
                    {es.assistant.restructureIntro(review.restructure.days_per_week)}
                  </p>
                  <div className="mt-3 flex flex-col gap-1.5">
                    {review.restructure.sessions.map((s) => (
                      <div key={s.name} className="flex items-baseline gap-2">
                        <span className="flex-1 truncate text-[14px]">{s.name}</span>
                        <span className="font-mono text-[13px] tabular-nums text-gris">
                          {s.total_sets} series · ~{s.minutes} min
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 border-t border-line pt-3 text-[13px] leading-snug">
                    <div>
                      {es.assistant.restructureKept(
                        review.restructure.sets_before,
                        review.restructure.sets_after,
                      )}
                    </div>
                    {review.restructure.trimmed.length > 0 && (
                      <div className="text-gris">
                        {es.assistant.restructureTrimmed(
                          review.restructure.trimmed.length,
                        )}
                      </div>
                    )}
                    <div
                      style={{
                        color: review.restructure.fits
                          ? "var(--green-text)"
                          : "var(--red-text)",
                      }}
                    >
                      {review.restructure.fits
                        ? es.assistant.restructureFits
                        : es.assistant.restructureDoesNotFit}
                    </div>
                    {review.restructure.under_target.length > 0 && (
                      <div className="text-gris">
                        {es.assistant.restructureUnder(
                          review.restructure.under_target
                            .map((m) => es.assistant.muscles[m] ?? m)
                            .join(", "),
                        )}
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={applyRestructure}
                    className="mt-4 h-touch w-full rounded-card border border-line text-sm text-blue"
                  >
                    {es.assistant.restructureApply}
                  </button>
                  <p className="mt-2 text-[12.5px] leading-snug text-gris">
                    {es.assistant.restructureNote}
                  </p>
                </Card>
              </section>
            )}

            <p className="text-[12.5px] leading-snug text-gris">
              {es.assistant.disclaimer}
            </p>

            <Button
              variant="primary"
              className="w-full"
              disabled={busy || accepted.size === 0}
              onClick={goReview}
            >
              {accepted.size === 0
                ? es.assistant.applyNone
                : es.assistant.applySelected(accepted.size)}
            </Button>
          </div>
        )}
      </div>

      {comparing && (
        <SwapCompare
          detail={(comparing.detail ?? {}) as Record<string, string>}
          why={say(es.assistant.why, comparing)}
          onClose={() => setComparing(null)}
        />
      )}
    </div>
  );
}
