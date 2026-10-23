"""
models/page.py
--------------
Pydantic schemas for page-level layout classification data.
"""

from pydantic import BaseModel


class PageProbabilities(BaseModel):
    text_heavy: float
    table: float
    figure: float
    mixed: float


class PageRecord(BaseModel):
    page_number: int
    page_type: str          # "text_heavy" | "table" | "figure" | "mixed"
    probabilities: PageProbabilities
    used_ocr: bool
