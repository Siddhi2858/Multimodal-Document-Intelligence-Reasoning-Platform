"""
scripts/test_rag.py
-------------------
Step 7 of Phase 3: full RAG loop in the terminal.

Usage (from the backend/ folder):
    python -m scripts.test_rag storage/uploads/Research_Paper.pdf
    python -m scripts.test_rag storage/uploads/Research_Paper.pdf --reingest

The PDF is only re-processed if it is not stored yet (or with --reingest).
Type  q  to quit.
"""

import sys

from ingestion.pipeline import ingest_pdf, make_document_id
from rag.answerer import answer_question
from retrieval.embedder import embed_query
from retrieval.vector_store import count_chunks, search

TOP_K = 5


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("Usage: python -m scripts.test_rag <path-to-pdf> [--reingest]")
        sys.exit(1)

    pdf_path = args[0]
    document_id = make_document_id(pdf_path)

    if "--reingest" in sys.argv or count_chunks(document_id) == 0:
        print("Ingesting PDF...")
        summary = ingest_pdf(pdf_path)
        print(f"Done: {summary['page_count']} pages, {summary['chunk_count']} chunks.")
    else:
        print(f"'{document_id}' already stored ({count_chunks(document_id)} chunks). Skipping ingestion.")

    while True:
        question = input("\nQuestion (q to quit): ").strip()
        if question.lower() in {"q", "quit", "exit"}:
            break
        if not question:
            continue

        chunks = search(embed_query(question), document_id=document_id, top_k=TOP_K)
        result = answer_question(question, chunks)

        if not result["found"]:
            print("\nAnswer: (not found in this document)")
            continue

        print(f"\nAnswer:\n{result['answer']}")
        print("\nRetrieved sources:")
        for c in result["sources"]:
            print(f"  page {c['page_number']}  score={c['score']}  [{c['chunk_id']}]")


if __name__ == "__main__":
    main()