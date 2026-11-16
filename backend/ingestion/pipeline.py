"""
ingestion/pipeline.py
---------------------
Runs the whole ingestion chain for one PDF:

    parse_pdf (+OCR for scans) -> chunk_document -> embed -> add_chunks (Qdrant)

It also saves the parsed pages, including text-block positions and OCR
confidence, to storage/parsed/<document_id>.json for the later phases
(layout, tables, highlighting).

Step 8 calls ingest_pdf() from the FastAPI upload route.
"""

import json
import re
import time
from pathlib import Path

from ingestion.chunker import chunk_document
from ingestion.pdf_parser import parse_pdf
from retrieval.embedder import embed
from retrieval.vector_store import add_chunks, delete_document

PARSED_DIR = Path(__file__).resolve().parent.parent / "storage" / "parsed"


def make_document_id(pdf_path: str | Path) -> str:
    """URL-safe id from the filename: 'Research Paper.pdf' -> 'research-paper'."""
    stem = Path(pdf_path).stem.lower()
    return re.sub(r"[^a-z0-9]+", "-", stem).strip("-")


def save_parsed_pages(document_id: str, filename: str, pages: list[dict]) -> Path:
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PARSED_DIR / f"{document_id}.json"
    path.write_text(
        json.dumps({"document_id": document_id, "filename": filename, "pages": pages}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def ingest_pdf(pdf_path: str | Path, document_id: str | None = None, ocr: bool = True) -> dict:
    """
    Process one PDF end to end and return a summary:
        document_id, page_count, chunk_count, seconds,
        ocr_pages        pages whose text came from OCR
        ocr_pending      scanned pages that could NOT be read (OCR missing or failed)
        ocr_confidence   average OCR confidence (None if no OCR was used)
        ocr_seconds      total time spent on OCR
        figure_count     pictures whose inner text was read (digital pages only)
        figure_chunks    chunks created from that text
        figure_seconds   total time spent on figure OCR
    Re-ingesting the same document replaces its old chunks.
    """
    started = time.time()
    document_id = document_id or make_document_id(pdf_path)

    pages = parse_pdf(pdf_path, ocr=ocr)
    chunks = chunk_document(document_id, pages)

    ocr_pages = [p for p in pages if p["source"] == "ocr"]
    pending = [p for p in pages if p["needs_ocr"]]

    if not chunks:
        if pending:
            reason = next((p["ocr_error"] for p in pending if p["ocr_error"]), "OCR could not run")
            raise ValueError(
                f"{len(pending)} scanned page(s) need OCR, but it could not run: {reason.splitlines()[0]}"
            )
        raise ValueError("No text could be found in this PDF.")

    vectors = embed([c["text"] for c in chunks])

    delete_document(document_id)  # avoid stale chunks from an older upload
    add_chunks(chunks, vectors)
    save_parsed_pages(document_id, Path(pdf_path).name, pages)

    confidences = [p["ocr_confidence"] for p in ocr_pages if p["ocr_confidence"] is not None]

    return {
        "document_id": document_id,
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "ocr_pages": [p["page_number"] for p in ocr_pages],
        "ocr_pending": [p["page_number"] for p in pending],
        "ocr_confidence": round(sum(confidences) / len(confidences), 3) if confidences else None,
        "ocr_seconds": round(sum(p["ocr_seconds"] or 0 for p in pages), 1),
        "figure_count": sum(len(p.get("figures") or []) for p in pages),
        "figure_chunks": sum(1 for c in chunks if c["source"] == "figure_ocr"),
        "figure_seconds": round(sum(p.get("figure_ocr_seconds") or 0 for p in pages), 1),
        "seconds": round(time.time() - started, 2),
    }