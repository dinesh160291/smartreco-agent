"""Backup of the system of record (POL-BACKUP-001).

The relational store is the only artefact here that cannot be rebuilt. The
vector index is re-derivable by construction (Core 20) and the catalog is
seeded from a file on every start, so a lost index costs a boot. A lost
database costs every journey, hypothesis and order the platform has recorded.

**Never a file copy.** In WAL mode recent commits live in the `-wal` sidecar,
so copying the main file silently omits them. Hit for real while taking a
backup during this build: the copy was short by 22 events and the mistake was
invisible until the counts were compared. `sqlite3`'s own backup API reads
through the WAL and produces a consistent file while the database is in use,
which is exactly the situation a scheduled backup runs in.
"""

import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_SQLITE_URL = re.compile(r"^sqlite:/{2,4}(?P<path>.+)$")


def database_path(database_url: str) -> Path | None:
    """The file behind a SQLAlchemy URL, or None when there isn't one.

    In-memory databases and non-SQLite backends have nothing to copy; a caller
    that gets None should skip rather than fail, because "no file" is a valid
    deployment (tests, or a future managed database) and not an error.
    """
    match = _SQLITE_URL.match(database_url)
    if not match:
        return None
    path = match.group("path")
    if ":memory:" in path:
        return None
    return Path(path)


def backup_database(database_url: str, destination_dir, keep: int,
                    stamp: str | None = None) -> Path | None:
    """Copy the database to `destination_dir`, keeping the newest `keep` files.

    Returns the file written, or None when the URL names nothing copyable.
    Rotation is bounded because an unbounded backup directory eventually fills
    the volume and takes down the database it was protecting.
    """
    source = database_path(database_url)
    if source is None or not source.exists():
        return None

    destination_dir = Path(destination_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = stamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    destination = destination_dir / f"{source.stem}-{stamp}.db"

    # Read-only on the source so a backup can never be the thing that corrupts
    # what it is protecting.
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(destination)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    existing = sorted(destination_dir.glob(f"{source.stem}-*.db"))
    for stale in existing[:-keep] if keep > 0 else existing:
        try:
            os.remove(stale)
        except OSError:
            pass                      # a locked or vanished file is not a failure
    return destination
