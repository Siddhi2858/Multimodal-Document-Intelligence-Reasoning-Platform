"""
models/qa.py
------------
Pydantic schemas for the question-answering endpoint.
"""

from pydantic import BaseModel


class AskRequest(BaseModel):
    """Body sent by the frontend when the user submits a question."""
    question: str


class QuestionSource(BaseModel):
    """A single source passage cited in an answer."""
    page_number: int
    chunk_id: str
    snippet: str          # short preview
    text: str = ""        # the full passage
    score: float
    top_offset: int


class QuestionResponse(BaseModel):
    """Full answer returned by the /ask endpoint."""
    found: bool
    answer: str
    sources: list[QuestionSource]