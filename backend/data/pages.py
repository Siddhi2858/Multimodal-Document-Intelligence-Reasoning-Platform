"""
data/pages.py
-------------
Per-document page classification data.

Each page record contains:
  page_number    – 1-indexed page number
  page_type      – dominant layout class
  probabilities  – model confidence scores for each class
  used_ocr       – True if optical character recognition was applied

Currently only doc-1 (the 20-page specimen) has detailed page data.
All other documents return a simplified flat list derived from their
page count.
"""

from models.page import PageRecord, PageProbabilities

# ---------------------------------------------------------------------------
# Detailed page data for doc-1 (matches frontend mockPages.ts)
# ---------------------------------------------------------------------------

def _build_doc1_pages() -> list[PageRecord]:
    pages: list[PageRecord] = []

    for idx in range(20):
        num = idx + 1
        page_type = "text_heavy"
        used_ocr = False
        probs = PageProbabilities(
            text_heavy=0.86, table=0.04, figure=0.03, mixed=0.07
        )

        if num == 1:
            page_type = "mixed"
            probs = PageProbabilities(
                text_heavy=0.22, table=0.08, figure=0.15, mixed=0.55
            )
        elif num in (4, 9):
            page_type = "figure"
            probs = PageProbabilities(
                text_heavy=0.12, table=0.08, figure=0.74, mixed=0.06
            )
        elif num in (8, 14):
            page_type = "table"
            probs = PageProbabilities(
                text_heavy=0.08, table=0.81, figure=0.04, mixed=0.07
            )
        elif num in (12, 16):
            page_type = "mixed"
            probs = PageProbabilities(
                text_heavy=0.25, table=0.20, figure=0.15, mixed=0.40
            )

        if num >= 18:
            used_ocr = True
            if num == 19:
                page_type = "table"
                probs = PageProbabilities(
                    text_heavy=0.15, table=0.77, figure=0.03, mixed=0.05
                )
            else:
                page_type = "text_heavy"
                probs = PageProbabilities(
                    text_heavy=0.84, table=0.05, figure=0.03, mixed=0.08
                )

        pages.append(
            PageRecord(
                page_number=num,
                page_type=page_type,
                probabilities=probs,
                used_ocr=used_ocr,
            )
        )

    return pages


DOC1_PAGES: list[PageRecord] = _build_doc1_pages()


# ---------------------------------------------------------------------------
# Generic page generator for any other document
# ---------------------------------------------------------------------------

def generate_pages(page_count: int) -> list[PageRecord]:
    """
    Return a simple page list for a document that has no detailed data.
    Alternates between text_heavy and mixed to look realistic.
    """
    pages: list[PageRecord] = []

    for idx in range(page_count):
        num = idx + 1
        if num % 7 == 0:
            page_type = "table"
            probs = PageProbabilities(
                text_heavy=0.10, table=0.78, figure=0.05, mixed=0.07
            )
        elif num % 5 == 0:
            page_type = "figure"
            probs = PageProbabilities(
                text_heavy=0.10, table=0.06, figure=0.75, mixed=0.09
            )
        elif num % 3 == 0:
            page_type = "mixed"
            probs = PageProbabilities(
                text_heavy=0.28, table=0.15, figure=0.18, mixed=0.39
            )
        else:
            page_type = "text_heavy"
            probs = PageProbabilities(
                text_heavy=0.85, table=0.05, figure=0.03, mixed=0.07
            )

        pages.append(
            PageRecord(
                page_number=num,
                page_type=page_type,
                probabilities=probs,
                used_ocr=(num >= page_count - 2),
            )
        )

    return pages


def get_pages_for_document(document_id: str, page_count: int) -> list[PageRecord]:
    """Return detailed or generated page data for a given document."""
    if document_id == "doc-1":
        return DOC1_PAGES
    return generate_pages(page_count)
