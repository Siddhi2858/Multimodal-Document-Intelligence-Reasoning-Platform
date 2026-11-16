"""
scripts/show_figures.py
-----------------------
What did figure OCR read inside each picture of a PDF?

Usage (from the backend/ folder):
    python -m scripts.show_figures storage/uploads/Research_Paper.pdf
    python -m scripts.show_figures storage/uploads/Research_Paper.pdf --find resubmission 2725 "standard queue"

--find reports, for every word or phrase, which page/figure contains it (or that no figure does).
"""

import argparse
import sys

from ingestion.pdf_parser import parse_pdf

parser = argparse.ArgumentParser()
parser.add_argument("pdf")
parser.add_argument("--find", nargs="*", default=[], help="words or phrases to look for in the figure text")
args = parser.parse_args()

pages = parse_pdf(args.pdf)
found_any = False
for page in pages:
    for number, figure in enumerate(page["figures"], start=1):
        found_any = True
        print(f"\n=== page {page['page_number']}, figure {number}  bbox {figure['bbox']}  "
              f"{figure['word_count']} words, confidence {figure['confidence']:.2f}")
        print(figure["text"])

if not found_any:
    sys.exit("No figure text was read (no pictures found, or OCR unavailable).")

for term in args.find:
    hits = [(p["page_number"], n) for p in pages for n, f in enumerate(p["figures"], 1) if term.lower() in f["text"].lower()]
    native = [p["page_number"] for p in pages if term.lower() in p["text"].lower()]
    print(f"\n'{term}': in figure text {hits or 'NOWHERE'};  in native page text on pages {native or 'NOWHERE'}")