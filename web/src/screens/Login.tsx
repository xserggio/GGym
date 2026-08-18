import { useState, type FormEvent } from "react";

import { Button } from "../components/Button";
import { Logo } from "../components/Logo";
import { es } from "../i18n/es";
import { ApiError, api, crossOrigin, setAuthToken, type UserOut } from "../lib/api";

interface LoginProps {
  onLogin: (user: UserOut) => void;
}

const REMEMBER_KEY = "gym.remember";

interface Remembered {
  username: string;
  password: string;
}

function loadRemembered(): Remembered | null {
  try {
    const raw = localStorage.getItem(REMEMBER_KEY);
    return raw ? (JSON.parse(raw) as Remembered) : null;
  } catch {
    return null;
  }
}

export function Login({ onLogin }: LoginProps) {
  const [saved] = useState(loadRemembered);
  const [username, setUsername] = useState(saved?.username ?? "");
  const [password, setPassword] = useState(saved?.password ?? "");
  const [remember, setRemember] = useState(saved !== null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await api.login(username, password);
      // Native builds have no shared cookie: keep the JWT for the Bearer header.
      if (crossOrigin) setAuthToken(user.token);
      try {
        if (remember) {
          localStorage.setItem(REMEMBER_KEY, JSON.stringify({ username, password }));
        } else {
          localStorage.removeItem(REMEMBER_KEY);
        }
      } catch {
        // storage unavailable (private mode) — non-fatal
      }
      onLogin(user);
    } catch (err) {
      setError(err instanceof ApiError ? es.login.error : String(err));
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-bg px-6">
      <form onSubmit={submit} className="flex w-full max-w-[320px] flex-col gap-4">
        <div className="mb-2 flex justify-center">
          <Logo size="hero" />
        </div>

        <label className="flex flex-col gap-1">
          <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-gris">
            {es.login.user}
          </span>
          <input
            name="username"
            autoComplete="username"
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
            name="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="h-touch rounded-field border border-line bg-paper px-3 text-ink"
          />
        </label>

        <label className="flex items-center gap-2 text-sm text-gris">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            className="h-4 w-4 accent-blue"
          />
          {es.login.remember}
        </label>

        {error && <p className="text-sm text-red">{error}</p>}

        <Button type="submit" variant="primary" disabled={busy} className="w-full">
          {busy ? es.login.loading : es.login.enter}
        </Button>
      </form>
    </div>
  );
}
