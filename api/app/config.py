"""Runtime configuration (pydantic-settings).

Environment variables use the GYM_ prefix, e.g. GYM_JWT_SECRET. `DATA_DIR` and
`database_url()` are kept as module-level names because Alembic's env.py imports
them directly.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# /api  (this file lives at /api/app/config.py)
API_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = API_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GYM_", env_file=".env", extra="ignore"
    )

    database_url: str = f"sqlite:///{(DATA_DIR / 'gym.db').as_posix()}"

    # Auth. The default secret is for local dev only; override in production.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 60 * 24 * 14  # 14 days

    cookie_name: str = "access_token"
    cookie_secure: bool = False  # True behind HTTPS in production
    cookie_samesite: str = "lax"
    # Path the auth cookie is scoped to. In production the app is served under a
    # subpath (e.g. /gym), so the cookie is scoped there.
    cookie_path: str = "/"

    # Origins the app is served from (CORS with credentials). The native
    # Capacitor build runs from the device itself: Android reports
    # http(s)://localhost, iOS capacitor://localhost. Without these the app
    # loads but every request fails at the preflight.
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost",
        "https://localhost",
        "capacitor://localhost",
    ]

    # Web push (spec §7.6). Empty keys disable sending; the settings UI then
    # reports that reminders are unavailable instead of failing silently.
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@example.com"

    # Reminder times are local wall-clock in this zone, independent of the
    # server's own timezone.
    timezone: str = "Europe/Madrid"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def database_url() -> str:
    return get_settings().database_url
