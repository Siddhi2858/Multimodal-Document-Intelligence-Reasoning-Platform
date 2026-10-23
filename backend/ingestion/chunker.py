"""
ingestion/chunker.py
--------------------
Step 3 of Phase 3: split page text into overlapping chunks.

Each chunk keeps its document_id and page_number, so every answer
can later be traced back to a page (this is what makes citations work).

Chunks never cross page boundaries. That keeps citations exact.
"""

import re

CHUNK_SIZE_WORDS = 120      # target words per chunk
CHUNK_OVERLAP_WORDS = 20    # words shared between neighbouring chunks
MIN_CHUNK_WORDS = 15        # drop tiny leftovers (page numbers, headers)


def clean_text(text: str) -> str:
    """Fix common PDF extraction problems."""
    # Join words split by a hyphen at a line end: "Ran-\ndom" -> "Random"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Turn remaining line breaks into spaces
    text = re.sub(r"\s*\n\s*", " ", text)
    # Collapse repeated spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def chunk_page(
    text: str,
    chunk_size: int = CHUNK_SIZE_WORDS,
    overlap: int = CHUNK_OVERLAP_WORDS,
) -> list[str]:
    """Split one page's text into overlapping word-based chunks."""
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = clean_text(text).split()
    if not words:
        return []

    chunks: list[str] = []
    step = chunk_size - overlap
    start = 0

    while start < len(words):
        piece = words[start : start + chunk_size]
        # Skip a tiny final piece unless it is the only chunk on the page
        if len(piece) >= MIN_CHUNK_WORDS or not chunks:
            chunks.append(" ".join(piece))
        if start + chunk_size >= len(words):
            break
        start += step

    return chunks


def chunk_document(document_id: str, pages: list[dict]) -> list[dict]:
    """
    Turn the output of parse_pdf() into a flat list of chunks:
        {"chunk_id": "doc1-p4-c2", "document_id": "doc1",
         "page_number": 4, "text": "..."}
    """
    all_chunks: list[dict] = []

    for page in pages:
        if page.get("needs_ocr"):
            continue  # nothing to chunk until Phase 4 (OCR)

        pieces = chunk_page(page["text"])
        for i, piece in enumerate(pieces, start=1):
            all_chunks.append(
                {
                    "chunk_id": f"{document_id}-p{page['page_number']}-c{i}",
                    "document_id": document_id,
                    "page_number": page["page_number"],
                    "text": piece,
                }
            )

    return all_chunks


if __name__ == "__main__":
    # Manual test:  python -m ingestion.chunker path/to/file.pdf
    import sys
    from collections import Counter
    from pathlib import Path

    from ingestion.pdf_parser import parse_pdf

    if len(sys.argv) < 2:
        print("Usage: python -m ingestion.chunker <path-to-pdf>")
        sys.exit(1)

    pdf = Path(sys.argv[1])
    chunks = chunk_document(pdf.stem.lower(), parse_pdf(pdf))

    print(f"Total chunks: {len(chunks)}")
    per_page = Counter(c["page_number"] for c in chunks)
    for page_no in sorted(per_page):
        print(f"  page {page_no}: {per_page[page_no]} chunks")

    sizes = [len(c["text"].split()) for c in chunks]
    print(f"Words per chunk: min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)//len(sizes)}")

    print("\n--- Sample chunk ---")
    sample = chunks[min(1, len(chunks) - 1)]
    print(sample["chunk_id"], f"(page {sample['page_number']})")
    print(sample["text"][:600])