"""
ocr/engine.py
-------------
Phase 4: read text from page images with Tesseract (through pytesseract).

ocr_image() returns, for one page image:
    text            the page text in reading order (Tesseract does the column analysis)
    blocks          one entry per text line: {"text", "bbox", "confidence", ...}
                    bbox = [x0, y0, x1, y1] in PDF points (1 pt = 1/72 inch)
    avg_confidence  mean word confidence, 0.0 to 1.0
    word_count

Tesseract is a separate program, not a pip package. On Windows install it from
https://github.com/UB-Mannheim/tesseract/wiki  (default folder is found automatically).
If it lives elsewhere, set the environment variable TESSERACT_CMD to the full path of tesseract.exe.
"""

import os
import shutil
from pathlib import Path

OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "eng")

_WINDOWS_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

INSTALL_HELP = (
    "Tesseract OCR is not installed (or not found).\n"
    "  Windows: install it from https://github.com/UB-Mannheim/tesseract/wiki, then restart the terminal.\n"
    "           If you installed it somewhere unusual, set TESSERACT_CMD to the full path of tesseract.exe.\n"
    "  Linux  : sudo apt install tesseract-ocr        macOS: brew install tesseract"
)


class OcrUnavailable(RuntimeError):
    """OCR cannot run on this machine (missing package or missing Tesseract)."""


_configured = False


def find_tesseract() -> str | None:
    """Locate the tesseract executable, or return None."""
    from_env = os.getenv("TESSERACT_CMD")
    if from_env and Path(from_env).exists():
        return from_env

    on_path = shutil.which("tesseract")
    if on_path:
        return on_path

    for candidate in _WINDOWS_PATHS:
        if Path(candidate).exists():
            return candidate
    return None


def _setup() -> None:
    global _configured
    if _configured:
        return

    try:
        import pytesseract
    except ImportError as error:
        raise OcrUnavailable("The 'pytesseract' package is missing. Run:  pip install pytesseract pillow") from error

    command = find_tesseract()
    if command is None:
        raise OcrUnavailable(INSTALL_HELP)

    pytesseract.pytesseract.tesseract_cmd = command
    _configured = True


def is_available() -> bool:
    try:
        _setup()
        return True
    except OcrUnavailable:
        return False


def version() -> str:
    _setup()
    import pytesseract

    return str(pytesseract.get_tesseract_version())


def ocr_image(image, dpi: int, lang: str | None = None) -> dict:
    """OCR one PIL image that was rendered at the given DPI."""
    _setup()
    import pytesseract

    data = pytesseract.image_to_data(
        image,
        lang=lang or OCR_LANGUAGE,
        config="--psm 3",  # fully automatic page segmentation (handles columns)
        output_type=pytesseract.Output.DICT,
    )

    scale = 72.0 / dpi  # pixels -> PDF points
    lines: dict[tuple, dict] = {}  # Tesseract's own order is the reading order
    all_confidences: list[float] = []

    for i, raw in enumerate(data["text"]):
        word = raw.strip()
        confidence = float(data["conf"][i])
        if not word or confidence < 0:  # -1 marks layout elements, not words
            continue

        left, top = data["left"][i], data["top"][i]
        right, bottom = left + data["width"][i], top + data["height"][i]
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])

        line = lines.setdefault(
            key,
            {"words": [], "confs": [], "x0": left, "y0": top, "x1": right, "y1": bottom,
             "block": key[0], "paragraph": key[1]},
        )
        line["words"].append(word)
        line["confs"].append(confidence)
        line["x0"], line["y0"] = min(line["x0"], left), min(line["y0"], top)
        line["x1"], line["y1"] = max(line["x1"], right), max(line["y1"], bottom)
        all_confidences.append(confidence)

    blocks = []
    text_parts: list[str] = []
    previous_paragraph = None

    for line in lines.values():
        line_text = " ".join(line["words"])
        paragraph = (line["block"], line["paragraph"])
        if previous_paragraph is not None and paragraph != previous_paragraph:
            text_parts.append("")  # blank line between paragraphs
        previous_paragraph = paragraph
        text_parts.append(line_text)

        blocks.append(
            {
                "text": line_text,
                "bbox": [round(line[k] * scale, 1) for k in ("x0", "y0", "x1", "y1")],
                "confidence": round(sum(line["confs"]) / len(line["confs"]) / 100, 3),
                "block": line["block"],
                "paragraph": line["paragraph"],
            }
        )

    average = sum(all_confidences) / len(all_confidences) / 100 if all_confidences else 0.0

    return {
        "text": "\n".join(text_parts).strip(),
        "blocks": blocks,
        "avg_confidence": round(average, 3),
        "word_count": len(all_confidences),
    }