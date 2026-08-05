import { es } from "../i18n/es";

export type Tab = "hoy" | "historial" | "rutina";

interface BottomNavProps {
  active: Tab;
  onSelect: (tab: Tab) => void;
}

const TABS: { key: Tab; label: string }[] = [
  { key: "hoy", label: es.nav.today },
  { key: "historial", label: es.nav.history },
  { key: "rutina", label: es.nav.routine },
];

/** Flat tab bar, no icons: a 2px rule marks the active destination (prototype).
 * Max four destinations (brief). */
export function BottomNav({ active, onSelect }: BottomNavProps) {
  return (
    <div className="grid grid-cols-3 border-t border-line bg-paper">
      {TABS.map((tab) => {
        const isActive = tab.key === active;
        return (
          <button
            key={tab.key}
            type="button"
            onClick={() => onSelect(tab.key)}
            className="-mt-px flex h-14 items-center justify-center border-t-2"
            style={{
              borderTopColor: isActive ? "var(--ink)" : "transparent",
              color: isActive ? "var(--ink)" : "var(--gris)",
            }}
          >
            <span className="font-mono text-[11px] tracking-[0.04em]">{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
