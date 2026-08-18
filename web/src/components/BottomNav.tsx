import { es } from "../i18n/es";

export type Tab = "inicio" | "hoy" | "historial" | "rutina";

interface BottomNavProps {
  active: Tab;
  onSelect: (tab: Tab) => void;
}

// Four destinations is the ceiling set by the brief.
const TABS: { key: Tab; label: string }[] = [
  { key: "inicio", label: es.nav.home },
  { key: "hoy", label: es.nav.today },
  { key: "historial", label: es.nav.history },
  { key: "rutina", label: es.nav.routine },
];

/** Flat tab bar, no icons: a 2px rule marks the active destination (prototype).
 * Max four destinations (brief). */
export function BottomNav({ active, onSelect }: BottomNavProps) {
  return (
    <div
      className="grid grid-cols-4 border-t border-line bg-paper"
      style={{ paddingBottom: "var(--safe-bottom)" }}
    >
      {TABS.map((tab) => {
        const isActive = tab.key === active;
        return (
          <button
            key={tab.key}
            type="button"
            onClick={() => onSelect(tab.key)}
            className="-mt-px flex h-14 items-center justify-center border-t-2"
            style={{
              borderTopColor: isActive ? "var(--blue)" : "transparent",
              color: isActive ? "var(--blue)" : "var(--gris)",
            }}
          >
            <span className="font-mono text-[11px] tracking-[0.04em]">{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
