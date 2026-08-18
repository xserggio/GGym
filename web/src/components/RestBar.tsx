import { es } from "../i18n/es";
import { mmss } from "../lib/format";

interface RestBarProps {
  seconds: number;
  onAdd: () => void;
  onSkip: () => void;
}

/** Floating rest countdown, pinned to the bottom, yellow while running. */
export function RestBar({ seconds, onAdd, onSkip }: RestBarProps) {
  return (
    <div
      className="absolute inset-x-3 flex items-center gap-2.5 rounded-card px-3 py-2.5"
      style={{
        background: "var(--yellow)",
        color: "#14161a",
        bottom: "calc(0.5rem + var(--safe-bottom))",
      }}
    >
      <span className="font-mono text-[10px] tracking-[0.06em]">{es.session.rest}</span>
      <span className="font-mono text-3xl font-bold leading-none tabular-nums">
        {mmss(seconds)}
      </span>
      <div className="ml-auto flex gap-1.5">
        <button
          type="button"
          onClick={onAdd}
          className="h-touch rounded-field border border-black/30 px-3 font-mono text-[13px]"
        >
          {es.session.addFifteen}
        </button>
        <button
          type="button"
          onClick={onSkip}
          className="h-touch rounded-field px-3 text-[13px]"
          style={{ background: "#14161a", color: "var(--paper)" }}
        >
          {es.session.skipRest}
        </button>
      </div>
    </div>
  );
}
