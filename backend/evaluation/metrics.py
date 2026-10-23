"""
evaluation/metrics.py
---------------------
Metric functions for the Phase 3 baseline (text-only RAG).

Everything here is page-level: retrieval returns chunks, chunks are mapped
to pages, and a page is "relevant" if it is listed in the question's
gold_pages.
"""

import re


def rank_pages(chunks: list[dict]) -> list[int]:
    """
    Turn a ranked list of retrieved chunks into a ranked list of distinct pages.
    A page takes the rank of its best-scoring chunk.
    """
    pages: list[int] = []
    for chunk in chunks:
        page = chunk["page_number"]
        if page not in pages:
            pages.append(page)
    return pages


def hit_at_k(ranked_pages: list[int], gold_pages: set[int], k: int) -> float:
    """1.0 if at least one relevant page is in the top k pages, else 0.0."""
    return 1.0 if gold_pages & set(ranked_pages[:k]) else 0.0


def recall_at_k(ranked_pages: list[int], gold_pages: set[int], k: int) -> float:
    """Fraction of the relevant pages that appear in the top k pages."""
    if not gold_pages:
        return 0.0
    return len(gold_pages & set(ranked_pages[:k])) / len(gold_pages)


def precision_at_k(ranked_pages: list[int], gold_pages: set[int], k: int) -> float:
    """Fraction of the top k pages that are relevant."""
    top = ranked_pages[:k]
    if not top:
        return 0.0
    return len(gold_pages & set(top)) / len(top)


def reciprocal_rank(ranked_pages: list[int], gold_pages: set[int]) -> float:
    """1 / rank of the first relevant page (0.0 if none was retrieved)."""
    for rank, page in enumerate(ranked_pages, start=1):
        if page in gold_pages:
            return 1.0 / rank
    return 0.0


def first_relevant_rank(ranked_pages: list[int], gold_pages: set[int]) -> int | None:
    """Rank (1-based) of the first relevant page, or None."""
    for rank, page in enumerate(ranked_pages, start=1):
        if page in gold_pages:
            return rank
    return None


def pages_mentioned(answer: str) -> set[int]:
    """Page numbers an answer cites in its text, e.g. '[page 4, page 5]'."""
    return {int(m) for m in re.findall(r"page\s+(\d+)", answer, flags=re.IGNORECASE)}


def keyword_hit(answer: str, keywords: list[str]) -> float:
    """
    Fraction of expected keywords found in the answer.
    Case-insensitive; thousands separators and spaces are ignored,
    so '1,400' matches '1400'.
    """
    if not keywords:
        return 1.0

    def normalise(text: str) -> str:
        return re.sub(r"[,\s]", "", text.lower())

    haystack = normalise(answer)
    found = sum(1 for keyword in keywords if normalise(keyword) in haystack)
    return found / len(keywords)


def citation_scores(answer: str, gold_pages: set[int]) -> dict:
    """
    How well the pages cited in the answer text match the gold pages.
      cited          – pages the answer names
      precision      – share of cited pages that are gold (None if nothing cited)
      supported      – True if the answer cites at least one page and all are gold
    Note: only as reliable as gold_pages is complete.
    """
    cited = pages_mentioned(answer)
    if not cited:
        return {"cited": [], "precision": None, "supported": False}
    correct = cited & gold_pages
    return {
        "cited": sorted(cited),
        "precision": len(correct) / len(cited),
        "supported": cited <= gold_pages,
    }


def mean(values: list[float]) -> float | None:
    """Average of a list, or None when the list is empty."""
    return sum(values) / len(values) if values else None