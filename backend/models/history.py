"""
models/history.py
-----------------
Pydantic schema for a past query history entry.
"""

from pydantic import BaseModel


class HistoryEntry(BaseModel):
    question: str
    asked_at: str
    pages: list[int]
    document_id: str = ""   # which document the question was asked about