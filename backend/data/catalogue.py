"""
data/catalogue.py
-----------------
Document catalogue stored in SQLite (see data/db.py).

Every document has:
  document_id       – unique slug used in URL routes
  filename          – original file name as uploaded
  title             – human-readable display title
  page_count        – total pages (0 until processing finishes)
  processing_status – "ready" | "processing" | "failed"
  created_at        – human-readable date/time string
  classification    – document type label
"""

from data.db import connect
from models.document import DocumentRecord

_COLUMNS = (
    "document_id, filename, title, page_count, "
    "processing_status, created_at, classification"
)


def get_all_documents() -> list[DocumentRecord]:
    """Return every document, oldest first."""
    conn = connect()
    try:
        rows = conn.execute(f"SELECT {_COLUMNS} FROM documents ORDER BY rowid").fetchall()
    finally:
        conn.close()
    return [DocumentRecord(**dict(row)) for row in rows]


def find_document(document_id: str) -> DocumentRecord | None:
    """Return the document with the given ID, or None if not found."""
    conn = connect()
    try:
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM documents WHERE document_id = ?", (document_id,)
        ).fetchone()
    finally:
        conn.close()
    return DocumentRecord(**dict(row)) if row else None


def add_document(document: DocumentRecord) -> DocumentRecord:
    """Add a document. Re-uploading the same ID replaces the old record."""
    conn = connect()
    try:
        conn.execute(
            f"""
            INSERT INTO documents ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                filename = excluded.filename,
                title = excluded.title,
                page_count = excluded.page_count,
                processing_status = excluded.processing_status,
                created_at = excluded.created_at,
                classification = excluded.classification
            """,
            (
                document.document_id, document.filename, document.title,
                document.page_count, document.processing_status,
                document.created_at, document.classification,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return document


def update_document(document_id: str, **fields) -> DocumentRecord | None:
    """Update fields of an existing document (e.g. status, page_count)."""
    allowed = {
        "filename", "title", "page_count",
        "processing_status", "created_at", "classification",
    }
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Unknown document fields: {sorted(unknown)}")

    if fields:
        assignments = ", ".join(f"{name} = ?" for name in fields)
        conn = connect()
        try:
            conn.execute(
                f"UPDATE documents SET {assignments} WHERE document_id = ?",
                (*fields.values(), document_id),
            )
            conn.commit()
        finally:
            conn.close()

    return find_document(document_id)