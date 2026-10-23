"""
data/db.py
----------
SQLite connection helper. The database is a single file at
backend/storage/folio.db and is created automatically on first use.

A new short-lived connection is opened per operation. That keeps it safe
to use from FastAPI's request threads and from background tasks.
"""

import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "storage" / "folio.db"

_init_lock = threading.Lock()
_initialised = False

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    document_id        TEXT PRIMARY KEY,
    filename           TEXT NOT NULL,
    title              TEXT NOT NULL,
    page_count         INTEGER NOT NULL DEFAULT 0,
    processing_status  TEXT NOT NULL,
    created_at         TEXT NOT NULL,
    classification     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    question  TEXT NOT NULL,
    asked_at  TEXT NOT NULL,      -- ISO timestamp; formatted when read
    pages     TEXT NOT NULL,      -- JSON list of page numbers
    document_id TEXT NOT NULL DEFAULT ''
);
"""


def _initialise(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    # Databases created before document_id existed get the column added.
    history_columns = {row[1] for row in conn.execute("PRAGMA table_info(history)")}
    if "document_id" not in history_columns:
        conn.execute("ALTER TABLE history ADD COLUMN document_id TEXT NOT NULL DEFAULT ''")
    # If the server stopped while a document was still processing, that job
    # is gone. Mark it failed instead of leaving it "processing" forever.
    conn.execute(
        "UPDATE documents SET processing_status = 'failed' "
        "WHERE processing_status = 'processing'"
    )
    conn.commit()


def connect() -> sqlite3.Connection:
    """Open a connection (creating the database and tables on first use)."""
    global _initialised

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row

    if not _initialised:
        with _init_lock:
            if not _initialised:
                _initialise(conn)
                _initialised = True
    return conn