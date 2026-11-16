"""
evaluation/scan_simulator.py
----------------------------
Turn a digital PDF into an image-only "scanned" PDF, at three quality levels.
This gives OCR a test with a known right answer: the original text layer.

    clean    200 dpi, high-quality image, perfectly straight
    typical  150 dpi, JPEG quality 60, tilted 0.4 degrees, light noise
    poor     100 dpi, JPEG quality 35, tilted 1.2 degrees, blur and heavy noise
"""

from io import BytesIO
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageFilter

CONDITIONS = {
    "clean": dict(dpi=200, jpeg_quality=95, rotate_deg=0.0, blur=0.0, noise=0.0),
    "typical": dict(dpi=150, jpeg_quality=60, rotate_deg=0.4, blur=0.0, noise=4.0),
    "poor": dict(dpi=100, jpeg_quality=35, rotate_deg=1.2, blur=0.8, noise=10.0),
}


def simulate_scan(src_pdf: str | Path, out_pdf: str | Path, condition: str, pages: list[int] | None = None, seed: int = 0) -> Path:
    """
    Write an image-only copy of src_pdf. `pages` (1-based) keeps only those pages, in order.
    The same seed always gives the same "scan", so results are reproducible.
    """
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition '{condition}'. Choose from {list(CONDITIONS)}")
    cfg = CONDITIONS[condition]
    rng = np.random.default_rng(seed)

    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    with pymupdf.open(src_pdf) as source, pymupdf.open() as scanned:
        for number, page in enumerate(source, start=1):
            if pages is not None and number not in pages:
                continue

            pixmap = page.get_pixmap(dpi=cfg["dpi"], colorspace=pymupdf.csGRAY)
            image = Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples)

            if cfg["rotate_deg"]:
                image = image.rotate(cfg["rotate_deg"], resample=Image.BICUBIC, fillcolor=255)
            if cfg["blur"]:
                image = image.filter(ImageFilter.GaussianBlur(cfg["blur"]))
            if cfg["noise"]:
                array = np.asarray(image, dtype=np.float32)
                array += rng.normal(0, cfg["noise"], array.shape)
                image = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))

            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=cfg["jpeg_quality"])

            new_page = scanned.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=buffer.getvalue())

        scanned.save(out_pdf, deflate=True)

    return out_pdf