"""Database setup — SQLite via SQLAlchemy, WAL mode (stack-decisions.md).

The engine is created from DATABASE_URL; WAL + foreign keys are enabled on every
connection. All multi-table writes happen inside session transactions (data-model
Integrity Rules).
"""

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///./data/smartreco.db"


class Base(DeclarativeBase):
    pass


def _sqlite_pragmas(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    # Wait for a busy database instead of failing instantly. SQLite defaults
    # busy_timeout to 0, and this app writes from request handlers and
    # background trigger evaluations concurrently, so contention is normal —
    # without this it surfaced as "database is locked" and killed a run.
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def make_engine(database_url: str | None = None):
    url = database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    if url.startswith("sqlite:///") and not url.endswith(":memory:"):
        db_path = Path(url.removeprefix("sqlite:///"))
        if db_path.parent != Path("."):
            db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    if url.startswith("sqlite"):
        event.listen(engine, "connect", _sqlite_pragmas)
    return engine


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
