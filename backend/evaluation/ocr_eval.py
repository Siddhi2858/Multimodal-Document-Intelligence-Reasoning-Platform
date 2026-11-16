"""
evaluation/ocr_eval.py
----------------------
Phase 4: how accurate is OCR? Compare it with the true text of a digital PDF.

For each quality level the script
  1. turns the PDF into an image-only "scan" (see scan_simulator.py),
  2. reads it back with OCR,
  3. compares the OCR text with the PDF's real text layer, page by page.

Usage (from the backend/ folder):
    python -m evaluation.ocr_eval storage/uploads/Research_Paper.pdf
    python -m evaluation.ocr_eval storage/uploads/Research_Paper.pdf --conditions clean typical --pages 1-3

Metrics (all normalised: lower case, one space between words, hyphenated line breaks joined):
    CER      character error rate: edit distance / number of true characters  (lower is better)
    WER      word error rate, same idea on words                              (lower is better)
    Word-F1  how many words were found, ignoring their ORDER                  (higher is better)
    Conf     Tesseract's own average confidence

CER and WER punish reading-order mistakes (for example two columns mixed up);
Word-F1 does not, and is closer to what retrieval needs.
Pages that contain figures are marked 'fig': OCR also reads the text INSIDE figures,
which the digital text layer does not contain, so their error looks worse than it is.
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pymupdf

from evaluation.metrics import mean
from evaluation.scan_simulator import CONDITIONS, simulate_scan
from ingestion.pdf_parser import parse_pdf

RESULTS_DIR = Path(__file__).resolve().parent / "results"
SCAN_DIR = Path(__file__).resolve().parent / "data" / "scanned"

try:
    from rapidfuzz.distance import Levenshtein
except ImportError:  # slow pure-Python fallback
    Levenshtein = None


def normalise(text: str) -> str:
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)          # join hyphenated line breaks
    text = text.replace("\u00ad", "")
    text = re.sub(r"[\u2018\u2019\u201a]", "'", text)
    text = re.sub(r"[\u201c\u201d\u201e]", '"', text)
    text = re.sub(r"[\u2010-\u2015\u2212]", "-", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def edit_distance(a, b) -> int:
    if Levenshtein is not None:
        return Levenshtein.distance(a, b)
    previous = list(range(len(b) + 1))  # fallback: classic dynamic programming
    for i, item_a in enumerate(a, start=1):
        current = [i]
        for j, item_b in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (item_a != item_b)))
        previous = current
    return previous[-1]


def page_scores(truth: str, ocr: str) -> dict:
    ref, hyp = normalise(truth), normalise(ocr)
    ref_words, hyp_words = ref.split(), hyp.split()

    overlap = sum((Counter(ref_words) & Counter(hyp_words)).values())
    precision = overlap / len(hyp_words) if hyp_words else 0.0
    recall = overlap / len(ref_words) if ref_words else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "cer": edit_distance(ref, hyp) / max(1, len(ref)),
        "wer": edit_distance(ref_words, hyp_words) / max(1, len(ref_words)),
        "word_f1": f1,
    }


def parse_page_list(spec: str | None, total: int) -> list[int] | None:
    if not spec:
        return None
    pages: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            start, end = part.split("-")
            pages.extend(range(int(start), int(end) + 1))
        else:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= total]


def pct(value) -> str:
    return "  n/a" if value is None else f"{value * 100:5.1f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure OCR accuracy against a digital PDF's real text.")
    parser.add_argument("pdf", help="a digital PDF with a text layer")
    parser.add_argument("--conditions", nargs="+", default=list(CONDITIONS), choices=list(CONDITIONS))
    parser.add_argument("--pages", help="only these pages, e.g. 1-3 or 2,5 (faster)")
    args = parser.parse_args()

    pdf = Path(args.pdf)
    if not pdf.exists():
        sys.exit(f"File not found: {pdf}")

    truth_pages = parse_pdf(pdf, ocr=False)
    selected = parse_page_list(args.pages, len(truth_pages)) or [p["page_number"] for p in truth_pages]
    truth = {p["page_number"]: p["text"] for p in truth_pages}

    with pymupdf.open(pdf) as doc:
        has_figure = {n: bool(doc[n - 1].get_images()) for n in selected}

    if Levenshtein is None:
        print("Note: 'rapidfuzz' is not installed, so scoring is slow. Install it with:  pip install rapidfuzz\n")

    report: dict = {"pdf": str(pdf), "pages": selected, "created": datetime.now().isoformat(timespec="seconds"), "conditions": {}}

    for condition in args.conditions:
        scan_path = simulate_scan(pdf, SCAN_DIR / f"{pdf.stem}_{condition}.pdf", condition, pages=selected)
        print(f"\n=== {condition.upper()}  ({CONDITIONS[condition]})")
        print(f"    scanned copy: {scan_path}")

        ocr_pages = parse_pdf(scan_path, ocr=True)
        rows = []
        print(f"    {'page':>4} {'':<4} {'CER':>7} {'WER':>7} {'Word-F1':>8} {'Conf':>6} {'sec':>6}")

        for original_number, ocr_page in zip(selected, ocr_pages):
            if not truth[original_number].strip():
                continue
            if ocr_page["needs_ocr"]:
                print(f"    {original_number:>4}  OCR could not run: {(ocr_page['ocr_error'] or '').splitlines()[0]}")
                sys.exit(1)

            scores = page_scores(truth[original_number], ocr_page["text"])
            row = {
                "page": original_number,
                "figure_on_page": has_figure[original_number],
                **{k: round(v, 4) for k, v in scores.items()},
                "confidence": ocr_page["ocr_confidence"],
                "seconds": ocr_page["ocr_seconds"],
            }
            rows.append(row)
            print(
                f"    {original_number:>4} {'fig' if row['figure_on_page'] else '':<4} {pct(row['cer']):>7} {pct(row['wer']):>7} "
                f"{pct(row['word_f1']):>8} {row['confidence'] or 0:>6.2f} {row['seconds'] or 0:>6.1f}"
            )

        no_fig = [r for r in rows if not r["figure_on_page"]]
        summary = {
            "pages_scored": len(rows),
            "cer": mean([r["cer"] for r in rows]),
            "wer": mean([r["wer"] for r in rows]),
            "word_f1": mean([r["word_f1"] for r in rows]),
            "cer_pages_without_figures": mean([r["cer"] for r in no_fig]),
            "word_f1_pages_without_figures": mean([r["word_f1"] for r in no_fig]),
            "avg_confidence": mean([r["confidence"] for r in rows if r["confidence"] is not None]),
            "avg_seconds_per_page": mean([r["seconds"] for r in rows if r["seconds"] is not None]),
        }
        print(
            f"    ALL PAGES      CER {pct(summary['cer'])}  WER {pct(summary['wer'])}  Word-F1 {pct(summary['word_f1'])}  "
            f"conf {summary['avg_confidence'] or 0:.2f}  {summary['avg_seconds_per_page'] or 0:.1f} s/page"
        )
        if no_fig and len(no_fig) < len(rows):
            print(f"    NO-FIGURE PAGES CER {pct(summary['cer_pages_without_figures'])}  Word-F1 {pct(summary['word_f1_pages_without_figures'])}")

        report["conditions"][condition] = {"settings": CONDITIONS[condition], "summary": summary, "pages": rows}

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"ocr-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved: {out}")
    print("Next: run your questions on a scanned copy, for example\n"
          f"  python -m evaluation.run_baseline --questions evaluation/questions_paper.json --document paper={SCAN_DIR / (pdf.stem + '_typical.pdf')}")


if __name__ == "__main__":
    main()