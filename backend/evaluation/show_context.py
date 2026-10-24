"""
evaluation/show_context.py
--------------------------
Look inside ONE question: which chunks were retrieved, which of them are sent to
the LLM, and whether the expected answer words are in them.

Usage (from the backend/ folder, API server stopped, after run_baseline has run once):
    python -m evaluation.show_context evaluation/questions_paper.json m01

It answers: "did retrieval fail to deliver the evidence, or did the model refuse
even though the evidence was there?"
"""

import sys
from pathlib import Path

from evaluation.metrics import keyword_hit
from evaluation.run_baseline import CONTEXT_CHUNKS, RETRIEVE_CHUNKS, load_test_set
from retrieval.embedder import embed_query
from retrieval.vector_store import count_chunks, search

EXCERPT_CHARS = 320


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -m evaluation.show_context <questions.json> <question id>")
        sys.exit(1)

    test_set = load_test_set(Path(sys.argv[1]))
    matches = [q for q in test_set["questions"] if q["id"] == sys.argv[2]]
    if not matches:
        ids = ", ".join(q["id"] for q in test_set["questions"])
        sys.exit(f"No question '{sys.argv[2]}'. Available: {ids}")

    question = matches[0]
    doc_id = f"eval-{question['document']}"
    if count_chunks(doc_id) == 0:
        sys.exit(f"Nothing is stored for '{doc_id}'. Run  python -m evaluation.run_baseline --questions {sys.argv[1]}  first.")

    gold = set(question.get("gold_pages", []))
    keywords = question.get("evidence_contains") or question.get("answer_contains", [])
    chunks = search(embed_query(question["question"]), document_id=doc_id, top_k=RETRIEVE_CHUNKS)

    print(f"\nQuestion : {question['question']}")
    print(f"Gold pages: {sorted(gold) or '(none: unanswerable)'}   Evidence words: {keywords or '-'}\n")

    sent_text = []
    for rank, chunk in enumerate(chunks, start=1):
        sent = rank <= CONTEXT_CHUNKS
        if sent:
            sent_text.append(chunk["text"])
        present = [k for k in keywords if keyword_hit(chunk["text"], [k]) == 1.0]
        flags = ("SENT TO LLM" if sent else "not sent").ljust(12) + ("  GOLD PAGE" if chunk["page_number"] in gold else "")
        print(f"{rank:>2}. page {chunk['page_number']}  score {chunk['score']:.2f}  {flags}  words here: {present or '-'}")
        print("    " + " ".join(chunk["text"].split())[:EXCERPT_CHARS] + "...\n")

    if keywords:
        coverage = keyword_hit(" ".join(sent_text), keywords)
        print(f"Words found in the text sent to the LLM: {coverage * 100:.0f}%")
        if coverage < 1.0:
            print("-> RETRIEVAL problem: the LLM was not given everything it needed.")
        else:
            print("-> The evidence WAS in the context. A refusal would be a generation/prompt problem.")


if __name__ == "__main__":
    main()