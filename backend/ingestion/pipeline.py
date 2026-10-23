"""
ingestion/pipeline.py
---------------------
Runs the whole ingestion chain for one PDF:

    parse_pdf -> chunk_document -> embed -> add_chunks (Qdrant)

Step 8 will call ingest_pdf() from the FastAPI upload route.
"""

import re
import time
from pathlib import Path

from ingestion.chunker import chunk_document
from ingestion.pdf_parser import parse_pdf
from retrieval.embedder import embed
from retrieval.vector_store import add_chunks, delete_document


def make_document_id(pdf_path: str | Path) -> str:
    """URL-safe id from the filename: 'Research Paper.pdf' -> 'research-paper'."""
    stem = Path(pdf_path).stem.lower()
    return re.sub(r"[^a-z0-9]+", "-", stem).strip("-")


def ingest_pdf(pdf_path: str | Path, document_id: str | None = None) -> dict:
    """
    Process one PDF end to end and return a small summary:
        {"document_id", "page_count", "chunk_count", "ocr_pages", "seconds"}
    Re-ingesting the same document replaces its old chunks.
    """
    started = time.time()
    document_id = document_id or make_document_id(pdf_path)

    pages = parse_pdf(pdf_path)
    chunks = chunk_document(document_id, pages)
    if not chunks:
        raise ValueError("No text could be extracted (scanned PDF? OCR comes in Phase 4).")

    vectors = embed([c["text"] for c in chunks])

    delete_document(document_id)  # avoid stale chunks from an older upload
    add_chunks(chunks, vectors)

    return {
        "document_id": document_id,
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "ocr_pages": [p["page_number"] for p in pages if p["needs_ocr"]],
        "seconds": round(time.time() - started, 2),
    }