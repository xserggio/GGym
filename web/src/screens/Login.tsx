import { useState, type FormEvent } from "react";

import { Button } from "../components/Button";
import { es } from "../i18n/es";
import { ApiError, api, type UserOut } from "../lib/api";

interface LoginProps {
  onLogin: (user: UserOut) => void;
}

export function Login({ onLogin }: LoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onLogin(await api.login(username, password));
    } catch (err) {
      setError(err instanceof ApiError ? es.login.error : String(err));
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-bg px-6">
      <form onSubmit={submit} className="flex w-full max-w-[320px] flex-col gap-4">
        <h1 className="font-display text-3xl">{es.app.title}</h1>

        <label className="flex flex-col gap-1">
          <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-gris">
            {es.login.user}
          </span>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoCapitalize="none"
            autoCorrect="off"
            className="h-touch rounded-field border border-line bg-paper px-3 text-ink"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-gris">
            {es.login.password}
          </span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="h-touch rounded-field border border-line bg-paper px-3 text-ink"
          />
        </label>

        {error && <p className="text-sm text-red">{error}</p>}

        <Button type="submit" variant="primary" disabled={busy} className="w-full">
          {busy ? es.login.loading : es.login.enter}
        </Button>
      </form>
    </div>
  );
}
