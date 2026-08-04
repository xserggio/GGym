"""Engine and session factory.

SQLite runs in WAL mode with foreign keys enforced. Both are set per-connection
because SQLite applies PRAGMAs at the connection level, not the database level.
"""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from .config import DATA_DIR, database_url


def _enable_sqlite_pragmas(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


def create_db_engine() -> Engine:
    url = database_url()
    if url.startswith("sqlite"):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, future=True)
    if url.startswith("sqlite"):
        _enable_sqlite_pragmas(engine)
    return engine


engine = create_db_engine()
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, future=True
)
