"""
scripts/test_retrieval.py
-------------------------
Step 6 of Phase 3: test retrieval on a real PDF before adding the LLM.

Usage (from the backend/ folder):
    python -m scripts.test_retrieval storage/uploads/Research_Paper.pdf

It ingests the PDF, then lets you type questions and shows the top
matching chunks with page numbers and scores. Type  q  to quit.
"""

import sys

from ingestion.pipeline import ingest_pdf
from retrieval.embedder import embed_query
from retrieval.vector_store import search

TOP_K = 5
SNIPPET_CHARS = 220


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.test_retrieval <path-to-pdf>")
        sys.exit(1)

    print("Ingesting PDF (first run loads the model)...")
    summary = ingest_pdf(sys.argv[1])
    print(
        f"Done: {summary['page_count']} pages, {summary['chunk_count']} chunks "
        f"in {summary['seconds']}s. OCR needed on pages: {summary['ocr_pages'] or 'none'}"
    )

    document_id = summary["document_id"]

    while True:
        question = input("\nQuestion (q to quit): ").strip()
        if question.lower() in {"q", "quit", "exit"}:
            break
        if not question:
            continue

        hits = search(embed_query(question), document_id=document_id, top_k=TOP_K)
        print(f"\nTop {len(hits)} results:")
        for rank, hit in enumerate(hits, start=1):
            text = hit["text"][:SNIPPET_CHARS].replace("\n", " ")
            print(f"  {rank}. page {hit['page_number']}  score={hit['score']}  [{hit['chunk_id']}]")
            print(f"     {text}...")


if __name__ == "__main__":
    main()