"""
ingestion/pdf_parser.py
-----------------------
Step 2 of Phase 3: extract text from a PDF, page by page.

Returns a list of dicts:
    [{"page_number": 1, "text": "...", "char_count": 1234, "needs_ocr": False}, ...]

Page numbers are 1-indexed so they match what the user sees in a PDF viewer.
"""

from pathlib import Path

import pymupdf  # PyMuPDF

# A page with fewer characters than this is probably a scanned image
# (or nearly blank). We flag it now so Phase 4 (OCR) knows where to look.
MIN_CHARS_FOR_TEXT_PAGE = 30


def parse_pdf(pdf_path: str | Path) -> list[dict]:
    """Extract text from every page of a PDF."""
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path.name}")

    pages: list[dict] = []

    with pymupdf.open(pdf_path) as doc:
        for index, page in enumerate(doc):
            text = page.get_text("text").strip()
            pages.append(
                {
                    "page_number": index + 1,
                    "text": text,
                    "char_count": len(text),
                    "needs_ocr": len(text) < MIN_CHARS_FOR_TEXT_PAGE,
                }
            )

    return pages


if __name__ == "__main__":
    # Quick manual test:  python -m ingestion.pdf_parser path/to/file.pdf
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m ingestion.pdf_parser <path-to-pdf>")
        sys.exit(1)

    result = parse_pdf(sys.argv[1])

    print(f"Total pages: {len(result)}")
    print(f"Pages likely needing OCR: {[p['page_number'] for p in result if p['needs_ocr']]}")
    print("-" * 60)

    for p in result[:3]:  # preview the first 3 pages
        print(f"\n=== Page {p['page_number']} ({p['char_count']} chars) ===")
        print(p["text"][:500])