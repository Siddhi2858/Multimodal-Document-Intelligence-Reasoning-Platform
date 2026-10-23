"""
evaluation/find_pages.py
------------------------
Helper for writing the test set: which pages of a PDF contain a word or number?

Usage (from the backend/ folder):
    python -m evaluation.find_pages storage/uploads/Research_Paper.pdf "93.42" "Firebase"

For every search term it lists the matching pages with a short excerpt, so you
can decide which pages belong in a question's gold_pages. Always confirm by
reading the page yourself.
"""

import re
import sys

from ingestion.pdf_parser import parse_pdf

EXCERPT_CHARS = 90


def main() -> None:
    if len(sys.argv) < 3:
        print('Usage: python -m evaluation.find_pages <pdf> "term" ["term" ...]')
        sys.exit(1)

    pages = parse_pdf(sys.argv[1])

    for term in sys.argv[2:]:
        print(f'\n=== "{term}" ===')
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        matched = False

        for page in pages:
            text = " ".join(page["text"].split())
            hits = list(pattern.finditer(text))
            if not hits:
                continue

            matched = True
            first = hits[0]
            start = max(0, first.start() - EXCERPT_CHARS // 2)
            excerpt = text[start : first.end() + EXCERPT_CHARS // 2]
            print(f"  page {page['page_number']:>2}  ({len(hits)}x)  ...{excerpt}...")

        if not matched:
            print("  (not found on any page)")


if __name__ == "__main__":
    main()