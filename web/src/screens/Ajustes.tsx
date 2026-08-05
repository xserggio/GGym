import { useState } from "react";

import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { es } from "../i18n/es";
import { api, type UserOut } from "../lib/api";

type Tema = "clara" | "oscura";

interface AjustesProps {
  user: UserOut;
  tema: Tema;
  onToggleTema: () => void;
  onBack: () => void;
  onLogout: () => void;
}

export function Ajustes({ user, tema, onToggleTema, onBack, onLogout }: AjustesProps) {
  const [exporting, setExporting] = useState(false);

  async function exportJson() {
    setExporting(true);
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `registro-fuerza-${user.username}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  const themeButton = (value: Tema, label: string) => {
    const active = tema === value;
    return (
      <button
        type="button"
        onClick={() => {
          if (!active) onToggleTema();
        }}
        className="h-touch flex-1 rounded-card border text-sm"
        style={{
          borderColor: active ? "var(--ink)" : "var(--line)",
          background: active ? "var(--ink)" : "transparent",
          color: active ? "var(--bg)" : "var(--ink)",
        }}
      >
        {label}
      </button>
    );
  };

  return (
    <div className="h-full overflow-y-auto px-4 pb-6 pt-4">
      <header className="mb-4 flex items-center">
        <h1 className="font-display text-3xl">{es.settings.title}</h1>
        <Button variant="ghost" onClick={onBack} className="ml-auto !min-h-0 !px-3 !py-1.5">
          {es.actions.back}
        </Button>
      </header>

      <div className="flex flex-col gap-4">
        <Card className="p-4">
          <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
            {es.settings.profile}
          </div>
          <div className="mt-2 text-lg font-medium">{user.display_name}</div>
          <div className="font-mono text-[11px] text-gris">{user.username}</div>
        </Card>

        <Card className="p-4">
          <div className="mb-2 font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
            {es.settings.appearance}
          </div>
          <div className="flex gap-2">
            {themeButton("clara", es.settings.light)}
            {themeButton("oscura", es.settings.dark)}
          </div>
        </Card>

        <Button variant="secondary" onClick={() => void exportJson()} disabled={exporting}>
          {exporting ? es.settings.exporting : es.settings.export}
        </Button>

        <Button variant="secondary" onClick={onLogout}>
          {es.settings.logout}
        </Button>
      </div>
    </div>
  );
}
