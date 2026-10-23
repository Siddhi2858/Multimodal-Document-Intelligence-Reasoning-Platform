"""
models/document.py
------------------
Pydantic schema for a document record.
"""

from pydantic import BaseModel


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    title: str
    page_count: int
    processing_status: str   # "ready" | "processing"
    created_at: str
    classification: str
