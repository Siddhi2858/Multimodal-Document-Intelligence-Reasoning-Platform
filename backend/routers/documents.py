"""
routers/documents.py
---------------------
Document management endpoints.

Routes:
  GET  /api/documents             → list all documents
  GET  /api/documents/{id}        → get one document
  POST /api/documents/upload      → simulate a PDF upload
  GET  /api/documents/{id}/pages  → get page-level data for a document
"""

import logging
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File

from models.document import DocumentRecord
from models.page import PageRecord
from data.catalogue import get_all_documents, find_document, add_document, update_document
from data.pages import get_pages_for_document
from ingestion.pipeline import ingest_pdf

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "storage" / "uploads"
MAX_UPLOAD_MB = 50

router = APIRouter(tags=["Documents"])


# ---------------------------------------------------------------------------
# List all documents
# ---------------------------------------------------------------------------

@router.get("/documents", response_model=list[DocumentRecord])
def list_documents():
    """
    Return every document in the library.

    The frontend Library page and Dashboard both use this endpoint to
    populate their document tables.
    """
    return get_all_documents()


# ---------------------------------------------------------------------------
# Get a single document
# ---------------------------------------------------------------------------

@router.get("/documents/{document_id}", response_model=DocumentRecord)
def get_document(document_id: str):
    """
    Return one document by its ID.

    Raises 404 if the document does not exist.
    """
    document = find_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    return document


# ---------------------------------------------------------------------------
# Upload a PDF (real processing runs in the background)
# ---------------------------------------------------------------------------

def _process_document(document_id: str, pdf_path: Path) -> None:
    """Background job: parse -> chunk -> embed -> store, then mark the document ready."""
    try:
        summary = ingest_pdf(pdf_path, document_id=document_id)
        update_document(
            document_id,
            page_count=summary["page_count"],
            processing_status="ready",
            classification="Text document (not yet classified)",
        )
    except Exception:
        logger.exception("Processing failed for %s", document_id)
        update_document(document_id, processing_status="failed")


@router.post("/documents/upload", response_model=DocumentRecord, status_code=201)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Accept a PDF, save it, and process it in the background.

    The response returns immediately with processing_status="processing".
    The frontend polls GET /api/documents/{id} until the status becomes
    "ready" (or "failed").

    Raises 400 for non-PDF or empty files, 413 if the file is too large.
    """
    filename = file.filename or "unknown.pdf"

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a .pdf file.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File is larger than {MAX_UPLOAD_MB} MB.")
    if not contents.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="This file does not look like a valid PDF.")

    # URL-safe document ID from the filename
    slug = re.sub(r"[^a-z0-9]+", "-", filename.lower().removesuffix(".pdf")).strip("-")
    document_id = f"upload-{(slug or 'document')[:40]}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    pdf_path.write_bytes(contents)

    title = filename.removesuffix(".pdf").replace("_", " ").replace("-", " ").strip()

    new_document = DocumentRecord(
        document_id=document_id,
        filename=filename,
        title=title,
        page_count=0,          # filled in when processing finishes
        processing_status="processing",
        created_at=datetime.now().strftime("%d %b %Y · %H:%M"),
        classification="Pending classification",
    )
    add_document(new_document)

    background_tasks.add_task(_process_document, document_id, pdf_path)
    return new_document


# ---------------------------------------------------------------------------
# Page-level breakdown
# ---------------------------------------------------------------------------

@router.get("/documents/{document_id}/pages", response_model=list[PageRecord])
def get_document_pages(document_id: str):
    """
    Return the page-type classification list for a document.

    For the specimen document (doc-1) this returns the detailed 20-page
    breakdown.  For any other document a reasonable set of pages is
    generated from the document's page count.

    Raises 404 if the document does not exist.
    """
    document = find_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    return get_pages_for_document(document_id, document.page_count)