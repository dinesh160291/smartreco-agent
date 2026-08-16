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
    #
    # **Raised from 5s to 30s after measuring.** SQLite allows one writer, and
    # a workflow run commits about a dozen times; with the instance ceiling at
    # 8 concurrent runs plus ingest from every open tab, the queue for the
    # writer is deep even though each transaction is short. At 50 concurrent
    # shoppers a 5-second ceiling produced 98 "database is locked" failures in
    # two minutes — 54 of them on event ingestion, which is a 500 in a
    # shopper's browser. Waiting is the right answer: the writer is never held
    # long, so a queued write completes in well under the new bound.
    cursor.execute("PRAGMA busy_timeout=30000")
    # WAL's documented companion. FULL fsyncs on every commit, which at this
    # commit rate is the cost that makes the queue deep in the first place.
    # NORMAL keeps WAL crash-safe for process and OS failure; the exposure it
    # accepts is losing the most recent transactions to a power cut, which for
    # this deployment is the right trade against refusing a shopper's events.
    cursor.execute("PRAGMA synchronous=NORMAL")
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
