"""
evaluation/compare_runs.py
--------------------------
Compare two result files from run_baseline: for example native PDF vs scanned copy,
or Baseline 1 vs a later improvement.

Usage (from the backend/ folder):
    python -m evaluation.compare_runs evaluation/results/A.json evaluation/results/B.json

It first checks that both runs used the SAME settings (chunk size, embedding model,
LLM, ...). If they differ, any difference in the numbers may come from the settings
and not from what you are comparing, and the script says so loudly.
"""

import json
import sys
from pathlib import Path

SETTINGS = ["chunk_size_words", "chunk_overlap_words", "embedding_model", "chunks_retrieved",
            "chunks_sent_to_llm", "llm_model", "min_retrieval_score"]

# Settings that you may change ON PURPOSE when the comparison is "before vs after one change".
# They are reported, but they do not trigger the warning. Older result files do not have the
# key, which means the feature did not exist yet, i.e. it was off.
# figure_chunk_words: runs saved before this setting existed used 120-word chunks for figure text.
CHANGE_UNDER_TEST = {"figure_ocr": False, "figure_chunk_words": 120}

ROWS = [
    ("Hit@1", "hit@1", True), ("Hit@3", "hit@3", True), ("Hit@5", "hit@5", True),
    ("Recall@5", "recall@5", True), ("Precision@5", "precision@5", True), ("MRR", "mrr", False),
    ("Context has the answer", "context_has_answer", True),
    ("Correct answers", "correct_rate", True), ("Answered when answerable", "answer_rate", True),
    ("Wrong answers (unanswerable)", "wrong_answer_rate", True),
    ("Pages sent to LLM", "avg_pages_processed", False), ("Words sent to LLM", "avg_context_words", False),
    ("Retrieval ms", "avg_retrieval_ms", False),
]


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fmt(value, percent: bool) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%" if percent else f"{value:.2f}" if value < 100 else f"{value:.0f}"


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("Usage: python -m evaluation.compare_runs <results A .json> <results B .json>")

    a, b = load(sys.argv[1]), load(sys.argv[2])
    name_a, name_b = Path(sys.argv[1]).stem, Path(sys.argv[2]).stem

    print(f"\nA = {name_a}\nB = {name_b}\n")

    differing = [(k, a["config"].get(k), b["config"].get(k)) for k in SETTINGS if a["config"].get(k) != b["config"].get(k)]
    tested = [(k, a["config"].get(k, d), b["config"].get(k, d)) for k, d in CHANGE_UNDER_TEST.items()
              if a["config"].get(k, d) != b["config"].get(k, d)]
    if differing:
        print("!" * 70)
        print("WARNING: the two runs used DIFFERENT SETTINGS. Differences in the numbers below")
        print("may come from these settings, not from the thing you want to compare:")
        for key, va, vb in differing:
            print(f"   {key}: A = {va!r}   B = {vb!r}")
        print("!" * 70 + "\n")
    else:
        print("Settings are identical (chunk size, embedding model, LLM): the comparison is fair.\n")

    if tested:
        print("Change under test (the ONLY setting that should differ):")
        for key, va, vb in tested:
            print(f"   {key}: A = {va!r}   B = {vb!r}")
        print()

    if a["config"].get("documents") != b["config"].get("documents"):
        print("Documents used:")
        print(f"   A: {a['config'].get('documents')}\n   B: {b['config'].get('documents')}\n")

    print(f"{'metric':<30}{'A':>10}{'B':>10}{'change':>10}")
    for label, key, percent in ROWS:
        va, vb = a["summary"].get(key), b["summary"].get(key)
        if va is None and vb is None:
            continue
        change = "" if va is None or vb is None else (f"{(vb - va) * 100:+.1f}" if percent else f"{vb - va:+.2f}")
        print(f"{label:<30}{fmt(va, percent):>10}{fmt(vb, percent):>10}{change:>10}")

    print("\nBy question type (Hit@1 / context has answer):")
    print(f"  {'type':<14}{'n':>3}{'A Hit@1':>10}{'B Hit@1':>10}{'A ctx':>9}{'B ctx':>9}")
    for t in sorted(set(a["by_type"]) | set(b["by_type"])):
        sa, sb = a["by_type"].get(t, {}), b["by_type"].get(t, {})
        print(f"  {t:<14}{sa.get('questions', sb.get('questions', 0)):>3}"
              f"{fmt(sa.get('hit@1'), True):>10}{fmt(sb.get('hit@1'), True):>10}"
              f"{fmt(sa.get('context_has_answer'), True):>9}{fmt(sb.get('context_has_answer'), True):>9}")

    qa = {q["id"]: q for q in a["questions"]}
    changes = []
    for q in b["questions"]:
        p = qa.get(q["id"])
        if p is None:
            continue
        notes = []
        if p.get("first_relevant_rank") != q.get("first_relevant_rank"):
            notes.append(f"first relevant page rank {p.get('first_relevant_rank')} -> {q.get('first_relevant_rank')}")
        if p.get("context_coverage") != q.get("context_coverage"):
            notes.append(f"context coverage {fmt(p.get('context_coverage'), True)} -> {fmt(q.get('context_coverage'), True)}")
        if p.get("found") != q.get("found") and "found" in p and "found" in q:
            notes.append(f"answered {p.get('found')} -> {q.get('found')}")
        if notes:
            changes.append((q["id"], q.get("type"), "; ".join(notes)))

    print(f"\nQuestions that changed ({len(changes)} of {len(b['questions'])}):")
    for qid, typ, note in changes:
        print(f"  {qid:<5}{typ:<13}{note}")
    if not changes:
        print("  none")


if __name__ == "__main__":
    main()