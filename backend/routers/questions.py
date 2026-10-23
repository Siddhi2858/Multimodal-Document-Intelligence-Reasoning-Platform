"""
routers/questions.py
---------------------
Question-answering endpoint.

Routes:
  POST /api/documents/{id}/ask  → ask a question about a document
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from models.qa import AskRequest, QuestionResponse, QuestionSource
from models.history import HistoryEntry
from data.catalogue import find_document
from data.history import add_to_history
from rag.answerer import answer_question
from retrieval.embedder import embed_query
from retrieval.vector_store import count_chunks, search

TOP_K = 5
SNIPPET_CHARS = 250


def _snippet(text: str) -> str:
    """Shorten a chunk to a readable snippet for the citation card."""
    text = " ".join(text.split())
    return text if len(text) <= SNIPPET_CHARS else text[:SNIPPET_CHARS].rstrip() + "..."


router = APIRouter(tags=["Questions"])


@router.post("/documents/{document_id}/ask", response_model=QuestionResponse)
def ask_question(document_id: str, body: AskRequest):
    """
    Answer a natural-language question about a document.

    How it works:
      1. The document must exist in the catalogue (404 if not).
      2. The document must be processed ("ready") and indexed, else 409.
      3. The question is embedded and the top chunks are retrieved.
      4. The LLM answers from those chunks only, with page citations.
      5. If the document does not contain the answer, found=False is
         returned so the frontend shows its "answer not found" state.
      6. Every question is added to the history store.

    Request body:
      { "question": "Your question here?" }
    """
    # Validate document exists
    document = find_document(document_id)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    question_text = body.question.strip()

    if not question_text:
        raise HTTPException(
            status_code=400,
            detail="Question must not be empty.",
        )

    # The document must be fully processed and indexed
    if document.processing_status != "ready" or count_chunks(document_id) == 0:
        raise HTTPException(
            status_code=409,
            detail="This document is not indexed yet. Upload a PDF and wait until processing finishes.",
        )

    # Retrieve -> generate
    try:
        chunks = search(embed_query(question_text), document_id=document_id, top_k=TOP_K)
        result = answer_question(question_text, chunks)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Answer generation failed: {exc}")

    response = QuestionResponse(
        found=result["found"],
        answer=result["answer"],
        sources=[
            QuestionSource(
                page_number=c["page_number"],
                chunk_id=c["chunk_id"],
                snippet=_snippet(c["text"]),
                text=" ".join(c["text"].split()),
                score=c["score"],
                top_offset=0,  # exact on-page position comes with layout analysis (Phase 5)
            )
            for c in result["sources"]
        ],
    )

    # Record in history (even not-found queries, so history stays useful)
    page_numbers = sorted({s.page_number for s in response.sources})
    add_to_history(
        HistoryEntry(
            question=question_text,
            asked_at=datetime.now().strftime("Today · %H:%M"),
            pages=page_numbers,
            document_id=document_id,
        )
    )

    return response