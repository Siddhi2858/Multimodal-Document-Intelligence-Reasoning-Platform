"""
evaluation/run_baseline.py
--------------------------
Step 10 of Phase 3: measure Baseline 1 (text-only RAG).

Usage (from the backend/ folder, with the API server STOPPED, because the local
vector store can only be opened by one program at a time):

    python -m evaluation.run_baseline                       # retrieval + efficiency only (free, fast)
    python -m evaluation.run_baseline --with-answers        # also generate answers with the LLM
    python -m evaluation.run_baseline --questions evaluation/questions.json --delay 4

What it does:
  1. Ingests every PDF listed in the questions file (parse -> chunk -> embed -> store).
  2. For each question, retrieves the top chunks exactly as the app does.
  3. Computes Hit@K, Recall@K, Precision@K and MRR on pages, plus context size and timing.
  4. With --with-answers it also asks the LLM and scores the answers.
  5. Saves everything (with the settings used) to evaluation/results/.
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from evaluation.metrics import (
    citation_scores,
    first_relevant_rank,
    hit_at_k,
    keyword_hit,
    mean,
    precision_at_k,
    rank_pages,
    recall_at_k,
    reciprocal_rank,
)
from ingestion.chunker import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from ingestion.pipeline import ingest_pdf
from retrieval import embedder
from retrieval.embedder import embed_query
from retrieval.vector_store import search

KS = (1, 3, 5)             # "top k pages" cut-offs reported
RETRIEVE_CHUNKS = 10       # chunks retrieved to build the page ranking
CONTEXT_CHUNKS = 5         # chunks the app really sends to the LLM (TOP_K in routers/questions.py)
TOKENS_PER_WORD = 1.3      # rough estimate; real tokenisers differ
RETRY_BASE_SECONDS = 10   # wait before retry n is 10, 20, 40 ... seconds

RESULTS_DIR = Path(__file__).resolve().parent / "results"


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def load_test_set(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))

    if "documents" not in data or "questions" not in data:
        raise ValueError('The questions file needs "documents" and "questions".')

    for question in data["questions"]:
        for field in ("id", "document", "question"):
            if field not in question:
                raise ValueError(f"Question is missing '{field}': {question}")
        if question["document"] not in data["documents"]:
            raise ValueError(
                f"{question['id']}: unknown document '{question['document']}'"
            )
        answerable = question.get("answerable", True)
        if answerable and not question.get("gold_pages"):
            raise ValueError(f"{question['id']}: answerable questions need gold_pages.")

    return data


# --------------------------------------------------------------------------
# One question
# --------------------------------------------------------------------------

def score_answer(record: dict, question: dict, gold: set, answerable: bool) -> None:
    """Score a stored answer (also used to re-score answers reused with --resume)."""
    if answerable and record.get("found"):
        record["keyword_hit"] = keyword_hit(record["answer"], question.get("answer_contains", []))
        cites = citation_scores(record["answer"], gold)
        record["cited_pages"] = cites["cited"]
        record["citation_precision"] = cites["precision"]
        record["citation_supported"] = cites["supported"]


def evaluate_question(
    question: dict,
    doc_id: str,
    with_answers: bool,
    delay: float,
    retries: int = 2,
    prior: dict | None = None,
    llm_enabled: bool = True,
) -> dict:
    gold = set(question.get("gold_pages", []))
    answerable = question.get("answerable", True)

    started = time.perf_counter()
    chunks = search(embed_query(question["question"]), document_id=doc_id, top_k=RETRIEVE_CHUNKS)
    retrieval_ms = (time.perf_counter() - started) * 1000

    ranked = rank_pages(chunks)
    context = chunks[:CONTEXT_CHUNKS]
    context_words = sum(len(c["text"].split()) for c in context)

    context_text = " ".join(c["text"] for c in context)
    keywords = question.get("answer_contains", [])
    # Optional stricter check: phrases that must appear in the text sent to the LLM.
    evidence = question.get("evidence_contains") or keywords

    record: dict = {
        "id": question["id"],
        "type": question.get("type", "factoid"),
        "question": question["question"],
        "answerable": answerable,
        "verified": question.get("verified", True),
        "gold_pages": sorted(gold),
        "retrieved_pages": ranked,
        "best_score": chunks[0]["score"] if chunks else None,
        "first_relevant_rank": first_relevant_rank(ranked, gold) if answerable else None,
        "pages_processed": len({c["page_number"] for c in context}),
        "context_words": context_words,
        "context_tokens_est": round(context_words * TOKENS_PER_WORD),
        "retrieval_ms": round(retrieval_ms, 1),
        "context_chunk_ids": [c["chunk_id"] for c in context],
    }

    if answerable and evidence:
        # Fraction of the evidence phrases (default: the expected answer words) found in the text sent to the LLM.
        record["context_coverage"] = keyword_hit(context_text, evidence)

    if answerable:
        record["rr"] = reciprocal_rank(ranked, gold)
        for k in KS:
            record[f"hit@{k}"] = hit_at_k(ranked, gold, k)
            record[f"recall@{k}"] = recall_at_k(ranked, gold, k)
            record[f"precision@{k}"] = precision_at_k(ranked, gold, k)

    if with_answers:
        record["found"] = None
        record["answer"] = ""
        record["error"] = None
        record["attempts"] = 0

        if prior is not None:
            # Reuse an answer that was generated successfully in an earlier run.
            record["found"] = prior["found"]
            record["answer"] = prior["answer"]
            record["answer_ms"] = prior.get("answer_ms")
            record["attempts"] = prior.get("attempts", 1)
            record["reused"] = True
            score_answer(record, question, gold, answerable)
        elif not llm_enabled:
            record["error"] = "skipped: the LLM kept failing, so no more answers were requested (re-run later with --resume)"
        else:
            from rag.answerer import answer_question  # imported here: needs the API key

            time.sleep(delay)
            for attempt in range(1, retries + 2):
                record["attempts"] = attempt
                print(f"      {question['id']}: asking the LLM (attempt {attempt} of {retries + 1})...", flush=True)
                started = time.perf_counter()
                try:
                    result = answer_question(question["question"], context)
                except Exception as exc:  # recorded, never hidden
                    record["error"] = f"{type(exc).__name__}: {exc}"
                    took = time.perf_counter() - started
                    print(f"      {question['id']}: failed after {took:.0f}s: {record['error'][:110]}", flush=True)
                    if attempt <= retries:
                        wait = RETRY_BASE_SECONDS * 2 ** (attempt - 1)
                        print(f"      {question['id']}: waiting {wait}s before trying again...", flush=True)
                        time.sleep(wait)
                    continue

                record["answer_ms"] = round((time.perf_counter() - started) * 1000, 1)
                print(f"      {question['id']}: answered in {record['answer_ms'] / 1000:.0f}s", flush=True)
                record["found"] = result["found"]
                record["answer"] = result["answer"]
                record["error"] = None
                score_answer(record, question, gold, answerable)
                break

    return record


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------

def summarise(records: list[dict], with_answers: bool) -> dict:
    answerable = [r for r in records if r["answerable"]]
    unanswerable = [r for r in records if not r["answerable"]]

    summary: dict = {
        "questions": len(records),
        "answerable": len(answerable),
        "unanswerable": len(unanswerable),
        "unverified": sum(1 for r in records if not r["verified"]),
        "mrr": mean([r["rr"] for r in answerable]),
    }

    for k in KS:
        for name in ("hit", "recall", "precision"):
            summary[f"{name}@{k}"] = mean([r[f"{name}@{k}"] for r in answerable])

    summary["context_has_answer"] = mean(
        [1.0 if r["context_coverage"] == 1.0 else 0.0 for r in answerable if "context_coverage" in r]
    )
    summary["avg_pages_processed"] = mean([r["pages_processed"] for r in records])
    summary["avg_context_words"] = mean([r["context_words"] for r in records])
    summary["avg_context_tokens_est"] = mean([r["context_tokens_est"] for r in records])
    summary["avg_retrieval_ms"] = mean([r["retrieval_ms"] for r in records])

    if with_answers:
        graded = [r for r in answerable if r.get("error") is None and r.get("found") is not None]
        answered = [r for r in graded if r["found"]]
        unans_graded = [r for r in unanswerable if r.get("error") is None and r.get("found") is not None]

        summary["graded_answerable"] = len(graded)
        summary["graded_unanswerable"] = len(unans_graded)
        summary["correct_rate"] = mean(
            [1.0 if r["found"] and r.get("keyword_hit") == 1.0 else 0.0 for r in graded]
        )
        times = sorted(r["answer_ms"] for r in records if r.get("answer_ms"))
        summary["median_answer_ms"] = times[len(times) // 2] if times else None
        summary["max_answer_ms"] = times[-1] if times else None
        summary["answer_rate"] = mean([1.0 if r["found"] else 0.0 for r in graded])
        summary["keyword_hit"] = mean([r["keyword_hit"] for r in answered if "keyword_hit" in r])
        summary["citation_precision"] = mean(
            [r["citation_precision"] for r in answered if r.get("citation_precision") is not None]
        )
        summary["citation_supported_rate"] = mean(
            [1.0 if r["citation_supported"] else 0.0 for r in answered if "citation_supported" in r]
        )
        summary["wrong_answer_rate"] = mean([1.0 if r["found"] else 0.0 for r in unans_graded])
        summary["avg_answer_ms"] = mean([r["answer_ms"] for r in records if "answer_ms" in r])
        summary["errors"] = sum(1 for r in records if r.get("error"))

    return summary


def group_by_type(records: list[dict], with_answers: bool) -> dict:
    types = sorted({r["type"] for r in records})
    return {t: summarise([r for r in records if r["type"] == t], with_answers) for t in types}


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def fmt(value, percent: bool = False) -> str:
    if value is None:
        return "  n/a"
    return f"{value * 100:5.1f}%" if percent else f"{value:5.2f}"


def print_report(summary: dict, by_type: dict, with_answers: bool) -> None:
    print("\n" + "=" * 70)
    print("BASELINE 1: TEXT-ONLY RAG")
    print("=" * 70)
    print(
        f"Questions: {summary['questions']}  "
        f"(answerable {summary['answerable']}, unanswerable {summary['unanswerable']})"
    )
    if summary["unverified"]:
        print(f"WARNING: {summary['unverified']} question(s) have verified=false. "
              "Check their gold pages before trusting these numbers.")

    print("\nRetrieval quality (answerable questions, page level)")
    print(f"  {'K':<4}{'Hit@K':>9}{'Recall@K':>11}{'Precision@K':>14}")
    for k in KS:
        print(
            f"  {k:<4}{fmt(summary[f'hit@{k}'], True):>9}"
            f"{fmt(summary[f'recall@{k}'], True):>11}"
            f"{fmt(summary[f'precision@{k}'], True):>14}"
        )
    print(f"  MRR: {fmt(summary['mrr'])}")
    print(
        f"  Context contains ALL expected answer words (top {CONTEXT_CHUNKS} chunks sent to the LLM): "
        f"{fmt(summary['context_has_answer'], True)}"
    )

    print("\nEfficiency (what is sent to the LLM per question)")
    print(f"  pages processed : {fmt(summary['avg_pages_processed'])}")
    print(f"  context words   : {summary['avg_context_words']:.0f}")
    print(f"  context tokens  : ~{summary['avg_context_tokens_est']:.0f}")
    print(f"  retrieval time  : {summary['avg_retrieval_ms']:.0f} ms")

    if with_answers:
        print(
            f"\nAnswers (based on {summary['graded_answerable']} of {summary['answerable']} answerable "
            f"and {summary['graded_unanswerable']} of {summary['unanswerable']} unanswerable questions)"
        )
        if summary.get("errors"):
            print(
                f"  WARNING: {summary['errors']} question(s) FAILED and are NOT counted in the "
                "percentages below. Read the 'error' field in the results file, fix the cause, and run again."
            )
        print(f"  CORRECT answers (answered + all expected keywords): {fmt(summary['correct_rate'], True)}   <- headline number")
        print(f"  answered when answerable     : {fmt(summary['answer_rate'], True)}")
        print(f"  expected keywords present    : {fmt(summary['keyword_hit'], True)}")
        print(f"  citation precision           : {fmt(summary['citation_precision'], True)}")
        print(f"  answers fully supported      : {fmt(summary['citation_supported_rate'], True)}")
        print(f"  wrong answers when unanswerable: {fmt(summary['wrong_answer_rate'], True)}")
        if summary.get("median_answer_ms") is not None:
            print(
                f"  answer time                  : median {summary['median_answer_ms'] / 1000:.1f}s, "
                f"slowest {summary['max_answer_ms'] / 1000:.1f}s  (depends on the LLM service's load)"
            )

    print("\nBy question type")
    header = f"  {'type':<14}{'n':>3}{'Hit@1':>9}{'Hit@3':>9}{'Hit@5':>9}{'MRR':>8}{'Context':>9}"
    print(header + (f"{'Correct':>10}" if with_answers else ""))
    for name, s in by_type.items():
        line = (
            f"  {name:<14}{s['questions']:>3}{fmt(s['hit@1'], True):>9}"
            f"{fmt(s['hit@3'], True):>9}{fmt(s['hit@5'], True):>9}{fmt(s['mrr']):>8}"
            f"{fmt(s['context_has_answer'], True):>9}"
        )
        if with_answers:
            line += f"{fmt(s.get('correct_rate'), True):>10}"
        print(line)


def save_results(config: dict, summary: dict, by_type: dict, records: list[dict]) -> tuple[Path, Path]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = RESULTS_DIR / f"baseline-{stamp}.json"
    csv_path = RESULTS_DIR / f"baseline-{stamp}.csv"

    json_path.write_text(
        json.dumps(
            {"config": config, "summary": summary, "by_type": by_type, "questions": records},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    columns = [
        "id", "type", "answerable", "verified", "gold_pages", "retrieved_pages",
        "first_relevant_rank", "rr", "hit@1", "hit@3", "hit@5", "recall@5", "precision@5",
        "best_score", "context_coverage", "pages_processed", "context_words", "context_tokens_est", "retrieval_ms",
        "found", "keyword_hit", "cited_pages", "citation_supported", "answer_ms", "attempts", "reused", "error",
        "question", "answer",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
            for key in ("gold_pages", "retrieved_pages", "cited_pages", "context_chunk_ids"):
                if key in row and row[key] is not None:
                    row[key] = " ".join(str(p) for p in row[key])
            writer.writerow(row)

    return json_path, csv_path


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def load_resume(path: Path, current_config: dict) -> dict[str, dict]:
    """Answers worth reusing from an earlier run: {question_id: record}."""
    previous = json.loads(path.read_text(encoding="utf-8"))
    old = previous["config"]

    for key in ("chunk_size_words", "chunk_overlap_words", "embedding_model", "llm_model"):
        if old.get(key) != current_config.get(key):
            raise SystemExit(
                f"Cannot resume: '{key}' differs (earlier run: {old.get(key)!r}, now: {current_config.get(key)!r}). "
                "Answers from different settings must not be mixed."
            )

    return {
        r["id"]: r
        for r in previous["questions"]
        if r.get("error") is None and r.get("found") is not None
    }


def run(
    questions_path: Path,
    with_answers: bool,
    delay: float,
    skip_ingest: bool,
    retries: int = 2,
    resume: Path | None = None,
    max_failures: int = 2,
) -> dict:
    test_set = load_test_set(questions_path)

    config = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "questions_file": str(questions_path),
        "documents": test_set["documents"],
        "chunk_size_words": CHUNK_SIZE_WORDS,
        "chunk_overlap_words": CHUNK_OVERLAP_WORDS,
        "embedding_model": embedder.MODEL_NAME,
        "chunks_retrieved": RETRIEVE_CHUNKS,
        "chunks_sent_to_llm": CONTEXT_CHUNKS,
        "with_answers": with_answers,
    }
    if with_answers:
        from rag import answerer
        config["llm_model"] = answerer.MODEL
        config["min_retrieval_score"] = answerer.MIN_RETRIEVAL_SCORE

    reusable: dict[str, dict] = {}
    if resume is not None:
        if not with_answers:
            raise SystemExit("--resume only makes sense together with --with-answers.")
        reusable = load_resume(resume, config)
        print(f"Resuming: {len(reusable)} earlier answer(s) will be reused, not requested again.")

    doc_ids: dict[str, str] = {}
    for key, pdf in test_set["documents"].items():
        doc_ids[key] = f"eval-{key}"
        if skip_ingest:
            continue
        print(f"Ingesting '{key}' ({pdf})...")
        summary = ingest_pdf(pdf, document_id=doc_ids[key])
        print(f"  {summary['page_count']} pages, {summary['chunk_count']} chunks")

    records = []
    total = len(test_set["questions"])
    llm_enabled = True
    consecutive_failures = 0

    for index, question in enumerate(test_set["questions"], start=1):
        prior = reusable.get(question["id"])
        if prior is not None and prior.get("question") != question["question"]:
            prior = None  # the question text changed, so the old answer does not apply

        record = evaluate_question(
            question, doc_ids[question["document"]], with_answers, delay, retries, prior, llm_enabled
        )
        records.append(record)

        rank = record["first_relevant_rank"]
        status = "unanswerable" if not record["answerable"] else (f"page rank {rank}" if rank else "MISS")
        coverage = record.get("context_coverage")
        ctx = "" if coverage is None else f"ctx {coverage * 100:3.0f}%"
        print(f"  [{index}/{total}] {record['id']:<8} {status:<14} {ctx:<9} {record['question'][:48]}")
        if record.get("reused"):
            print("      (answer reused from the earlier run)")
        elif record.get("error") and record["attempts"]:
            print(f"      ERROR after {record['attempts']} attempt(s): {record['error'][:220]}")

        if with_answers and not record.get("reused") and llm_enabled:
            if record.get("error"):
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    llm_enabled = False
                    print(
                        f"\n  >>> {consecutive_failures} questions in a row failed. Not asking the LLM again in this run "
                        "(its quota or service is probably exhausted).\n"
                        "  >>> Retrieval results are still computed. Re-run later with:  --resume <this run's .json file>\n"
                    )
            else:
                consecutive_failures = 0

    summary = summarise(records, with_answers)
    by_type = group_by_type(records, with_answers)

    return {"config": config, "summary": summary, "by_type": by_type, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the text-only RAG baseline.")
    parser.add_argument("--questions", default="evaluation/questions.json", help="test set JSON file")
    parser.add_argument("--with-answers", action="store_true", help="also generate and score LLM answers")
    parser.add_argument("--delay", type=float, default=2.0, help="seconds to wait before each LLM call")
    parser.add_argument("--retries", type=int, default=2, help="extra attempts when an LLM call fails")
    parser.add_argument("--resume", help="earlier results .json: reuse its successful answers, request only the missing ones")
    parser.add_argument("--max-failures", type=int, default=2, help="stop asking the LLM after this many failures in a row")
    parser.add_argument("--skip-ingest", action="store_true", help="reuse chunks already stored from a previous run")
    args = parser.parse_args()

    questions_path = Path(args.questions)
    if not questions_path.exists():
        print(f"Questions file not found: {questions_path}")
        sys.exit(1)

    outcome = run(
        questions_path, args.with_answers, args.delay, args.skip_ingest, args.retries,
        Path(args.resume) if args.resume else None, args.max_failures,
    )
    print_report(outcome["summary"], outcome["by_type"], args.with_answers)

    json_path, csv_path = save_results(
        outcome["config"], outcome["summary"], outcome["by_type"], outcome["records"]
    )
    print(f"\nSaved:\n  {json_path}\n  {csv_path}")


if __name__ == "__main__":
    main()