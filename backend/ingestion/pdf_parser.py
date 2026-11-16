"""
ingestion/pdf_parser.py
-----------------------
Phase 3 + 4: get the text of every page, using OCR for scanned pages.

Every page comes back in ONE schema, whether its text is native or from OCR:

    page_number     1-based
    text            the page text
    char_count
    source          "native" | "ocr" | "empty"
    needs_ocr       True only if the page is a scan that could NOT be read (OCR missing or failed)
    ocr_applied     True if OCR was run on this page
    ocr_confidence  0.0-1.0 average word confidence (OCR pages only, else None)
    ocr_seconds     time OCR took (OCR pages only)
    ocr_error       why OCR could not be used (else None)
    width, height   page size in PDF points
    blocks          [{"text", "bbox": [x0, y0, x1, y1], "confidence"}]  text blocks/lines with
                    positions in PDF points; "confidence" is None for native text
    figures         [{"bbox", "text", "word_count", "confidence"}]  text read INSIDE embedded pictures
                    (diagram labels, chart text) by OCR. Kept apart from "text" so the page text stays
                    clean; the chunker turns each figure into its own chunk (source "figure_ocr").
    figure_ocr_seconds  time spent on figure OCR for this page (None if not run)

A page is treated as a scan when it has (almost) no text layer but contains images,
or when one image covers most of the page and only a little text sits on top of it.
"""

import logging
import os
import time
from pathlib import Path

import pymupdf

logger = logging.getLogger(__name__)

OCR_DPI = 200                      # resolution pages are rendered at for OCR
MIN_CHARS_FOR_TEXT_PAGE = 30       # fewer native characters than this + an image => scanned
HYBRID_MAX_NATIVE_CHARS = 150      # a mostly-image page with less text than this => scanned
SCAN_IMAGE_COVERAGE = 0.6          # share of the page one or more images must cover
OCR_DESKEW = True                  # straighten tilted scans before OCR (see ocr/preprocess.py)

# OCR of pictures inside digital pages (see ocr/figures.py). Switch off with  FIGURE_OCR=0
# to reproduce "Baseline 1" exactly.
FIGURE_OCR = os.getenv("FIGURE_OCR", "1") != "0"
FIGURE_MIN_WIDTH_PT = 100          # smaller pictures are logos and icons, not figures
FIGURE_MIN_HEIGHT_PT = 60
FIGURE_MAX_PAGE_SHARE = 0.85       # a picture covering more than this is a page scan, not a figure
FIGURE_MAX_PER_PAGE = 6            # the largest N pictures of a page are read
FIGURE_MIN_WORDS = 2               # a figure with fewer recognised words is ignored


def _image_coverage(page) -> float:
    """Share of the page area covered by images (0.0 to 1.0)."""
    page_area = page.rect.width * page.rect.height
    if page_area <= 0:
        return 0.0
    covered = 0.0
    for info in page.get_image_info():
        visible = pymupdf.Rect(info["bbox"]) & page.rect
        covered += max(0.0, visible.width) * max(0.0, visible.height)
    return min(1.0, covered / page_area)


def _native_blocks(page) -> list[dict]:
    blocks = []
    for x0, y0, x1, y1, text, _number, kind in page.get_text("blocks"):
        if kind != 0 or not text.strip():  # kind 1 = image block
            continue
        blocks.append(
            {"text": " ".join(text.split()), "bbox": [round(v, 1) for v in (x0, y0, x1, y1)], "confidence": None}
        )
    return blocks


def _looks_scanned(native_chars: int, has_images: bool, coverage: float) -> bool:
    if has_images and native_chars < MIN_CHARS_FOR_TEXT_PAGE:
        return True
    return coverage >= SCAN_IMAGE_COVERAGE and native_chars < HYBRID_MAX_NATIVE_CHARS


def _render_for_ocr(page):
    """Render the page for OCR. Returns (PIL image, degrees of tilt that were corrected)."""
    import numpy as np
    from PIL import Image

    pixmap = page.get_pixmap(dpi=OCR_DPI, colorspace=pymupdf.csGRAY)
    gray = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width)

    correction = 0.0
    if OCR_DESKEW:
        from ocr.preprocess import deskew

        gray, correction = deskew(gray)

    return Image.fromarray(gray), correction


def _figure_regions(page) -> list:
    """Rectangles (PDF points) of the embedded pictures on a page that are big enough to be figures."""
    page_area = page.rect.width * page.rect.height
    found: list = []
    for info in page.get_image_info():
        rect = pymupdf.Rect(info["bbox"]) & page.rect
        if rect.is_empty or rect.width < FIGURE_MIN_WIDTH_PT or rect.height < FIGURE_MIN_HEIGHT_PT:
            continue
        if rect.width * rect.height > FIGURE_MAX_PAGE_SHARE * page_area:
            continue
        if any((rect & other).get_area() > 0.8 * rect.get_area() for other in found):
            continue  # the same picture listed twice, or one inside another
        found.append(rect)
    found.sort(key=lambda r: -r.get_area())
    return found[:FIGURE_MAX_PER_PAGE]


def _ocr_figures(page) -> list[dict]:
    """OCR the text inside each figure of a digital page. Raises OcrUnavailable if Tesseract is missing."""
    import numpy as np

    from ocr.figures import FIGURE_DPI, ocr_figure

    figures = []
    for rect in _figure_regions(page):
        # Rendering the clip (not extracting the image) also captures vector overlays and masks.
        pixmap = page.get_pixmap(dpi=FIGURE_DPI, clip=rect, colorspace=pymupdf.csGRAY)
        gray = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width)
        result = ocr_figure(gray)
        if result["word_count"] >= FIGURE_MIN_WORDS:
            figures.append(
                {
                    "bbox": [round(v, 1) for v in (rect.x0, rect.y0, rect.x1, rect.y1)],
                    "text": result["text"],
                    "word_count": result["word_count"],
                    "confidence": result["avg_confidence"],
                }
            )
    return figures


def parse_pdf(pdf_path: str | Path, ocr: bool = True) -> list[dict]:
    """Extract every page of a PDF (OCR on scanned pages unless ocr=False)."""
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path.name}")

    pages: list[dict] = []
    ocr_unavailable_reason: str | None = None  # once OCR is known to be missing, do not retry per page

    with pymupdf.open(pdf_path) as doc:
        for index, page in enumerate(doc):
            native_text = page.get_text("text").strip()
            coverage = _image_coverage(page)
            has_images = bool(page.get_images(full=True))

            record = {
                "page_number": index + 1,
                "text": native_text,
                "char_count": len(native_text),
                "source": "native" if native_text else "empty",
                "needs_ocr": False,
                "ocr_applied": False,
                "ocr_confidence": None,
                "ocr_seconds": None,
                "ocr_error": None,
                "ocr_deskew_degrees": None,
                "width": round(page.rect.width, 1),
                "height": round(page.rect.height, 1),
                "blocks": _native_blocks(page),
                "figures": [],
                "figure_ocr_seconds": None,
            }

            if _looks_scanned(len(native_text), has_images, coverage):
                record["needs_ocr"] = True

                if not ocr:
                    record["ocr_error"] = "OCR was turned off"
                elif ocr_unavailable_reason:
                    record["ocr_error"] = ocr_unavailable_reason
                else:
                    try:
                        from ocr.engine import OcrUnavailable, ocr_image

                        started = time.perf_counter()
                        image, correction = _render_for_ocr(page)
                        result = ocr_image(image, dpi=OCR_DPI)
                        record["ocr_deskew_degrees"] = correction
                        seconds = round(time.perf_counter() - started, 2)
                        text = result["text"].strip()

                        record["ocr_applied"] = True
                        record["ocr_seconds"] = seconds

                        if len(text) >= len(native_text) and text:
                            record.update(
                                text=text,
                                char_count=len(text),
                                source="ocr",
                                needs_ocr=False,
                                ocr_confidence=result["avg_confidence"],
                                blocks=result["blocks"],
                            )
                        elif native_text:
                            record["needs_ocr"] = False  # OCR found less than the text layer: keep native
                        else:
                            record.update(source="empty", needs_ocr=False)  # a blank scan
                    except Exception as error:  # OcrUnavailable or an OCR failure
                        reason = str(error) if error.__class__.__name__ == "OcrUnavailable" else f"{type(error).__name__}: {error}"
                        record["ocr_error"] = reason
                        if error.__class__.__name__ == "OcrUnavailable":
                            ocr_unavailable_reason = reason
                            logger.warning("OCR unavailable: %s", reason.splitlines()[0])
                        else:
                            logger.exception("OCR failed on page %s", index + 1)

            # Digital page: also read the text inside its pictures (never on pages already read by OCR).
            if ocr and FIGURE_OCR and not ocr_unavailable_reason and not record["ocr_applied"] and not record["needs_ocr"]:
                try:
                    started = time.perf_counter()
                    record["figures"] = _ocr_figures(page)
                    record["figure_ocr_seconds"] = round(time.perf_counter() - started, 2)
                except Exception as error:  # figure OCR must never break ingestion of the page text
                    if error.__class__.__name__ == "OcrUnavailable":
                        ocr_unavailable_reason = str(error)
                        logger.warning("OCR unavailable, figure text skipped: %s", ocr_unavailable_reason.splitlines()[0])
                    else:
                        logger.exception("Figure OCR failed on page %s", index + 1)

            pages.append(record)

    return pages


if __name__ == "__main__":
    # Quick manual test:  python -m ingestion.pdf_parser path/to/file.pdf
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m ingestion.pdf_parser <path-to-pdf>")
        sys.exit(1)

    result = parse_pdf(sys.argv[1])

    print(f"Total pages: {len(result)}")
    print(f"Read with OCR       : {[p['page_number'] for p in result if p['source'] == 'ocr']}")
    print(f"Could NOT be read   : {[p['page_number'] for p in result if p['needs_ocr']]}")
    print(f"Blank               : {[p['page_number'] for p in result if p['source'] == 'empty' and not p['needs_ocr']]}")
    print(f"Figures with text   : {sum(len(p['figures']) for p in result)} (pages {[p['page_number'] for p in result if p['figures']]})")
    blocked = {p["ocr_error"] for p in result if p["ocr_error"]}
    for reason in blocked:
        print(f"OCR problem: {reason.splitlines()[0]}")
    print("-" * 60)

    for p in result[:3]:  # preview the first 3 pages
        confidence = "" if p["ocr_confidence"] is None else f", confidence {p['ocr_confidence']:.2f}"
        print(f"\n=== Page {p['page_number']} ({p['char_count']} chars, {p['source']}{confidence}) ===")
        print(p["text"][:500])