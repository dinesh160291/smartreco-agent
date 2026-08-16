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
    # The pool must not be smaller than the number of threads that can ask for
    # a connection. SQLAlchemy's default (5 + 10 overflow = 15) is well under
    # the server's 40-thread pool, so a burst of ordinary reads queues for a
    # *connection* rather than for data — and then fails.
    #
    # Measured against a deliberately slow provider: background runs waiting on
    # a call hold their connection, and requests died with "QueuePool limit of
    # size 5 overflow 10 reached, connection timed out" after waiting the full
    # 30 seconds. The provider was not the fault; it only made an
    # already-undersized pool visible.
    #
    # SQLite connections are cheap — a file handle and a small cache — so
    # sizing past the thread pool costs little and removes the queue entirely.
    # In-memory SQLite uses a SingletonThreadPool, which takes none of these
    # and needs none of them — there is one connection by construction.
    pool_args = {} if url.endswith(":memory:") else {
        "pool_size": 25, "max_overflow": 25, "pool_timeout": 30}
    engine = create_engine(url, connect_args={"check_same_thread": False},
                           **pool_args)
    if url.startswith("sqlite"):
        event.listen(engine, "connect", _sqlite_pragmas)
    return engine


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
