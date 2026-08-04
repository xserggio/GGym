"""Runtime configuration.

Kept intentionally small for phase 1: a single SQLite database path,
overridable through the DATABASE_URL environment variable. Pydantic-settings
takes over in phase 3 when the API and auth land.
"""
from __future__ import annotations

import os
from pathlib import Path

# /api  (this file lives at /api/app/config.py)
API_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = API_DIR / "data"


def database_url() -> str:
    """SQLite file by default; override with DATABASE_URL for tests or Postgres."""
    override = os.environ.get("DATABASE_URL")
    if override:
        return override
    return f"sqlite:///{(DATA_DIR / 'gym.db').as_posix()}"
