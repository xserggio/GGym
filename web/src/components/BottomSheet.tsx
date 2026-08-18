import type { ReactNode } from "react";

import { es } from "../i18n/es";

interface BottomSheetProps {
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
}

/** Modal sheet anchored to the bottom, over a scrim. */
export function BottomSheet({ title, subtitle, onClose, children }: BottomSheetProps) {
  return (
    <div
      className="absolute inset-0 z-20 flex items-end"
      style={{ background: "rgba(20,22,26,0.35)" }}
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
        className="max-h-[80%] w-full overflow-y-auto rounded-t-sheet bg-bg px-4 pb-6 pt-4"
        style={{ paddingBottom: "calc(1.5rem + var(--safe-bottom))" }}
      >
        <div className="mb-1 flex items-baseline gap-2">
          <span className="font-display text-2xl">{title}</span>
          {subtitle && <span className="font-mono text-[11px] text-gris">{subtitle}</span>}
          <button
            type="button"
            onClick={onClose}
            className="ml-auto h-9 rounded-card border border-line px-3 text-[13px] text-ink"
          >
            {es.actions.close}
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
