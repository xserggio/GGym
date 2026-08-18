import { useEffect, useState } from "react";

import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Header } from "../components/Header";
import { es } from "../i18n/es";
import { api, type NotificationOut, type PhasesOut, type UserOut } from "../lib/api";
import { disablePush, enablePush, isStandalone, pushSupported } from "../lib/push";

type Tema = "clara" | "oscura";

interface AjustesProps {
  user: UserOut;
  onPhases: () => void;
  tema: Tema;
  onToggleTema: () => void;
  onBack: () => void;
  onLogout: () => void;
}

export function Ajustes({ user, tema, onToggleTema, onBack, onLogout, onPhases }: AjustesProps) {
  const [exporting, setExporting] = useState(false);
  const [notif, setNotif] = useState<NotificationOut | null>(null);
  const [notifBusy, setNotifBusy] = useState(false);
  const [notifNote, setNotifNote] = useState("");
  const [phases, setPhases] = useState<PhasesOut | null>(null);

  useEffect(() => {
    api.notifications().then(setNotif).catch(() => undefined);
    api.phases().then(setPhases).catch(() => undefined);
  }, []);

  /** Permission first, then persist: a switch that says "on" while the browser
   * blocks notifications would be a lie. */
  async function toggleNotif(enabled: boolean) {
    if (!notif) return;
    setNotifBusy(true);
    setNotifNote("");
    try {
      if (enabled) {
        if (!pushSupported()) {
          setNotifNote(isStandalone() ? es.notifications.unsupported : es.notifications.installFirst);
          return;
        }
        if (!(await enablePush(notif.vapid_public_key))) {
          setNotifNote(es.notifications.denied);
          return;
        }
      } else {
        await disablePush();
      }
      setNotif(
        await api.setNotifications({
          enabled,
          hour: notif.hour,
          minute: notif.minute,
        }),
      );
    } finally {
      setNotifBusy(false);
    }
  }

  async function changeTime(value: string) {
    if (!notif) return;
    const [rawHour, rawMinute] = value.split(":");
    const hour = Number(rawHour);
    const minute = Number(rawMinute);
    if (!Number.isInteger(hour) || !Number.isInteger(minute)) return;
    setNotif({ ...notif, hour, minute });
    setNotif(await api.setNotifications({ enabled: notif.enabled, hour, minute }));
  }

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
    <div className="flex h-full flex-col">
      <Header
        title={es.settings.title}
        leading={
          <Button variant="ghost" onClick={onBack} className="mb-1 !min-h-0 !px-3 !py-1.5">
            {es.actions.back}
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-4 pb-6 pt-4">

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

        {notif && (
          <Card className="p-4">
            <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
              {es.notifications.title}
            </div>
            {notif.vapid_public_key === "" ? (
              <p className="mt-2 text-sm text-gris">{es.notifications.unavailable}</p>
            ) : (
              <>
                <label className="mt-3 flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={notif.enabled}
                    disabled={notifBusy}
                    onChange={(e) => void toggleNotif(e.target.checked)}
                    className="h-5 w-5 flex-none accent-blue"
                  />
                  <span className="text-sm">{es.notifications.enable}</span>
                </label>

                {notif.enabled && (
                  <div className="mt-3 flex items-center gap-3">
                    <span className="font-mono text-[11px] text-gris">
                      {es.notifications.time}
                    </span>
                    <input
                      type="time"
                      value={`${String(notif.hour).padStart(2, "0")}:${String(
                        notif.minute,
                      ).padStart(2, "0")}`}
                      onChange={(e) => void changeTime(e.target.value)}
                      className="h-touch rounded-field border border-line bg-paper px-3 font-mono text-sm text-ink"
                    />
                  </div>
                )}

                <p className="mt-3 text-[13px] leading-snug text-gris">
                  {notifBusy ? es.notifications.saving : es.notifications.explain}
                </p>
                {notifNote && (
                  <p className="mt-2 text-[13px] leading-snug text-red">{notifNote}</p>
                )}
                {notif.enabled && notif.devices > 0 && (
                  <p className="mt-1 font-mono text-[11px] text-gris">
                    {es.notifications.devices(notif.devices)}
                  </p>
                )}
              </>
            )}
          </Card>
        )}

        {phases && (
          <Card className="p-4">
            <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-gris">
              {es.phases.title}
            </div>
            <label className="mt-3 flex items-center gap-3">
              <input
                type="checkbox"
                checked={phases.enabled}
                onChange={(e) =>
                  void api.setPhasesEnabled(e.target.checked).then(setPhases)
                }
                className="h-5 w-5 flex-none accent-blue"
              />
              <span className="text-sm">{es.phases.enable}</span>
            </label>
            <p className="mt-3 text-[13px] leading-snug text-gris">{es.phases.explain}</p>
            {phases.enabled && (
              <Button variant="secondary" onClick={onPhases} className="mt-3 w-full">
                {es.phases.open}
              </Button>
            )}
          </Card>
        )}

        <Button variant="secondary" onClick={() => void exportJson()} disabled={exporting}>
          {exporting ? es.settings.exporting : es.settings.export}
        </Button>

        <Button variant="secondary" onClick={onLogout}>
          {es.settings.logout}
        </Button>
      </div>
    </div>
    </div>
  );
}
