"""
data/history.py
---------------
Query history stored in SQLite (see data/db.py).

Each question is saved with a real timestamp. When history is read, the
timestamp is shown the way the frontend expects:
"Today · 10:14", "Yesterday", or "12 Oct".
"""

import json
from datetime import datetime

from data.db import connect
from models.history import HistoryEntry

MAX_ENTRIES = 100


def _format_asked_at(iso_timestamp: str) -> str:
    asked = datetime.fromisoformat(iso_timestamp)
    days_ago = (datetime.now().date() - asked.date()).days
    if days_ago == 0:
        return asked.strftime("Today · %H:%M")
    if days_ago == 1:
        return "Yesterday"
    return f"{asked.day} {asked.strftime('%b')}"


def get_history() -> list[HistoryEntry]:
    """Return history entries, newest first."""
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT question, asked_at, pages, document_id FROM history ORDER BY id DESC LIMIT ?",
            (MAX_ENTRIES,),
        ).fetchall()
    finally:
        conn.close()

    return [
        HistoryEntry(
            question=row["question"],
            asked_at=_format_asked_at(row["asked_at"]),
            pages=json.loads(row["pages"]),
            document_id=row["document_id"],
        )
        for row in rows
    ]


def add_to_history(entry: HistoryEntry) -> None:
    """Save a question. The time is recorded now, whatever entry.asked_at says."""
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO history (question, asked_at, pages, document_id) VALUES (?, ?, ?, ?)",
            (
                entry.question,
                datetime.now().isoformat(timespec="seconds"),
                json.dumps(entry.pages),
                entry.document_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()