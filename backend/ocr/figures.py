"""
ocr/figures.py
--------------
Read the text INSIDE figures (diagram boxes, chart labels, screenshots) of a digital PDF.

Why a separate step: a digital PDF's text layer does not contain text that is part of an
embedded picture. Running OCR on the whole page does not fix this either: small labels in
a diagram are lost among the large page. In tests, whole-page OCR found 0 of 9 small coloured
labels, while OCR on the cropped figure found 8 or 9.

Settings (chosen by testing on diagrams with small white-on-colour and dark-on-light labels):
    * crop the figure and render it at 300 dpi            (labels are tiny on the page)
    * Tesseract page mode 11 ("sparse text")              (labels are scattered, not paragraphs)
    * read the image normal AND inverted                  (white text on a dark box needs the inverse)
    * read at 1x AND 2x size, keep the more confident reading of each word
    * NO thresholding or denoising                        (adaptive thresholding dropped 7 of 9 labels;
                                                           it erases thin strokes, as in preprocess.py)
"""

import numpy as np
import cv2

from ocr import engine

FIGURE_DPI = 300
UPSCALE = 2                  # second reading at this scale factor
MAX_UPSCALE_PIXELS = 6_000_000   # do not upscale very large figures (slow, no gain)
MIN_WORD_CONFIDENCE = 40     # Tesseract confidence (0-100) below which a word is thrown away
PSM = 11


def _read(gray: np.ndarray, scale: float, lang: str) -> list[dict]:
    """One OCR pass. Boxes are returned in the coordinates of the un-scaled image."""
    import pytesseract

    data = pytesseract.image_to_data(
        gray, lang=lang, config=f"--psm {PSM}", output_type=pytesseract.Output.DICT
    )
    words = []
    for i, raw in enumerate(data["text"]):
        text = raw.strip()
        confidence = float(data["conf"][i])
        if not text or confidence < MIN_WORD_CONFIDENCE:
            continue
        left, top = data["left"][i] / scale, data["top"][i] / scale
        words.append(
            {"text": text, "conf": confidence, "x0": left, "y0": top,
             "x1": left + data["width"][i] / scale, "y1": top + data["height"][i] / scale}
        )
    return words


def _is_noise(text: str) -> bool:
    """Single stray characters and pure symbols are almost always OCR junk in a figure."""
    keep = [c for c in text if c.isalnum()]
    return not keep or (len(keep) == 1 and not keep[0].isdigit())


def _centre_inside(a: dict, b: dict) -> bool:
    cx, cy = (a["x0"] + a["x1"]) / 2, (a["y0"] + a["y1"]) / 2
    return b["x0"] <= cx <= b["x1"] and b["y0"] <= cy <= b["y1"]


def _merge(candidates: list[dict]) -> list[dict]:
    """Several passes read the same word; keep only the most confident reading per location."""
    accepted: list[dict] = []
    for word in sorted(candidates, key=lambda w: -w["conf"]):
        if _is_noise(word["text"]):
            continue
        if any(_centre_inside(word, a) or _centre_inside(a, word) for a in accepted):
            continue
        accepted.append(word)
    return accepted


FRAGMENT_GAP = 1.5   # a horizontal gap wider than this many text heights starts a new fragment


def _in_reading_order(words: list[dict]) -> str:
    """
    One FRAGMENT per line: rows are read top to bottom, left to right, and a row is cut wherever
    there is a wide gap. In a diagram a wide gap means "next box", so neighbouring boxes are no
    longer mixed into one sentence ("District 2725 Deduplication Stochastic noise ...").
    """
    if not words:
        return ""
    heights = sorted(w["y1"] - w["y0"] for w in words)
    height = max(4.0, heights[len(heights) // 2])

    rows: list[list[dict]] = []
    for word in sorted(words, key=lambda w: (w["y0"] + w["y1"]) / 2):
        centre = (word["y0"] + word["y1"]) / 2
        if rows and abs(centre - np.mean([(w["y0"] + w["y1"]) / 2 for w in rows[-1]])) <= 0.6 * height:
            rows[-1].append(word)
        else:
            rows.append([word])

    lines: list[str] = []
    for row in rows:
        row = sorted(row, key=lambda w: w["x0"])
        fragment = [row[0]]
        for previous, word in zip(row, row[1:]):
            if word["x0"] - previous["x1"] > FRAGMENT_GAP * height:
                lines.append(" ".join(w["text"] for w in fragment))
                fragment = []
            fragment.append(word)
        lines.append(" ".join(w["text"] for w in fragment))
    return "\n".join(lines)


def ocr_figure(gray: np.ndarray, lang: str | None = None) -> dict:
    """
    OCR one figure given as a grayscale array rendered at FIGURE_DPI.
    Returns {"text", "word_count", "avg_confidence"} (confidence 0.0-1.0).
    """
    engine._setup()
    lang = lang or engine.OCR_LANGUAGE

    images = [(gray, 1.0), (255 - gray, 1.0)]
    if gray.size <= MAX_UPSCALE_PIXELS:
        big = cv2.resize(gray, None, fx=UPSCALE, fy=UPSCALE, interpolation=cv2.INTER_CUBIC)
        images += [(big, float(UPSCALE)), (255 - big, float(UPSCALE))]

    candidates: list[dict] = []
    for image, scale in images:
        candidates += _read(image, scale, lang)

    words = _merge(candidates)
    return {
        "text": _in_reading_order(words),
        "word_count": len(words),
        "avg_confidence": round(sum(w["conf"] for w in words) / len(words) / 100, 3) if words else 0.0,
    }