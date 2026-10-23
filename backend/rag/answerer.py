"""
rag/answerer.py
---------------
Step 7 of Phase 3: generate an answer from retrieved chunks using an LLM.

Flow:
    question + retrieved chunks  ->  prompt  ->  Claude  ->  answer

The model is told to use ONLY the provided sources. If the sources do
not contain the answer, it must reply NOT_FOUND, and we return found=False.

Setup: put your key in backend/.env as
    ANTHROPIC_API_KEY=sk-ant-...
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from google.genai import types

load_dotenv()

MODEL = "gemini-3.8-flash"
MAX_TOKENS = 1000
MIN_RETRIEVAL_SCORE = 0.20
RETRY_WAITS_SECONDS = (2, 5)   # waits before retry 1 and 2 on a temporary Gemini error   # below this, skip the LLM: nothing relevant was found

SYSTEM_PROMPT = """You answer questions about a document using ONLY the numbered sources provided.

Rules:
- Use only information that appears in the sources. Do not use outside knowledge.
- Be concise and direct.
- After each claim, cite the page it came from like this: [page 4].
- If the sources do not contain the answer, reply with exactly: NOT_FOUND"""

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("GEMINI_API_KEY not found. Create backend/.env containing:\nGEMINI_API_KEY=your-key")
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def _is_temporary(error: Exception) -> bool:
    """503 'high demand' and 429 'too many requests' usually pass within seconds."""
    if isinstance(error, errors.ServerError):
        return True
    return isinstance(error, errors.ClientError) and getattr(error, "code", None) == 429


def _generate_with_retry(**kwargs):
    """Call Gemini, retrying a couple of times if it is temporarily overloaded."""
    for wait in RETRY_WAITS_SECONDS:
        try:
            return _get_client().models.generate_content(**kwargs)
        except Exception as error:
            if not _is_temporary(error):
                raise
            time.sleep(wait)
    return _get_client().models.generate_content(**kwargs)  # last attempt: errors propagate


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks as numbered sources with their page numbers."""
    blocks = [
        f"[Source {i} | page {c['page_number']}]\n{c['text']}"
        for i, c in enumerate(chunks, start=1)
    ]
    return "\n\n".join(blocks)


def answer_question(question: str, chunks: list[dict]) -> dict:
    """
    Returns:
        {"found": bool, "answer": str, "sources": chunks_used}
    """
    # Nothing retrieved, or everything scored too low: don't spend an LLM call.
    if not chunks or max(c["score"] for c in chunks) < MIN_RETRIEVAL_SCORE:
        return {"found": False, "answer": "", "sources": []}

    user_message = f"Sources:\n\n{build_context(chunks)}\n\nQuestion: {question}"

    response = _generate_with_retry(
        model=MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0,
            max_output_tokens=MAX_TOKENS,
        ),
    )
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response (blocked or out of tokens).")

    if text.upper().startswith("NOT_FOUND"):
        return {"found": False, "answer": "", "sources": []}

    return {"found": True, "answer": text, "sources": chunks}