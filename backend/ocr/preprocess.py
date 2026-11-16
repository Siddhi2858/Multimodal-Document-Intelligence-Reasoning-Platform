"""
ocr/preprocess.py
-----------------
Image clean-up before OCR. Only deskew (straightening a tilted scan) is used:
tests on a poor scan showed it cuts the OCR error from 55% to 19%, while
denoising and black-and-white thresholding made the result much WORSE
(they erase the thin strokes of small text).

The tilt is found with a projection profile: when text lines are perfectly
horizontal, the rows of the page are either full of ink or empty, which makes
the row-sums vary the most. We try small angles and keep the one that varies most.
"""

import cv2
import numpy as np

MAX_TILT_DEGREES = 3.0     # only correct small tilts; bigger angles are probably not scan tilt
MIN_TILT_DEGREES = 0.2     # below this, leave the image alone
SEARCH_STEP = 0.1
ANALYSIS_WIDTH = 900       # the angle is measured on a shrunken copy (fast)


def _rotate(image: np.ndarray, degrees: float, fill: int = 0) -> np.ndarray:
    height, width = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), degrees, 1.0)
    return cv2.warpAffine(image, matrix, (width, height), flags=cv2.INTER_CUBIC, borderValue=fill)


def estimate_tilt(gray: np.ndarray) -> float:
    """The rotation in degrees (positive = counter-clockwise) that makes the text lines
    horizontal, or 0.0 if unsure. Rotating the page by this amount straightens it."""
    scale = ANALYSIS_WIDTH / gray.shape[1]
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else gray
    _, ink = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    if ink.mean() < 1.0:  # almost no ink: blank page or photo, nothing to measure
        return 0.0

    def sharpness(angle: float) -> float:
        rows = _rotate(ink, angle).sum(axis=1).astype(np.float64)
        return float(rows.var())

    angles = np.arange(-MAX_TILT_DEGREES, MAX_TILT_DEGREES + SEARCH_STEP / 2, SEARCH_STEP)
    scores = [sharpness(a) for a in angles]
    best = float(angles[int(np.argmax(scores))])

    # If the best angle is barely better than "no rotation", the measurement is not trustworthy.
    if sharpness(best) < sharpness(0.0) * 1.02:
        return 0.0
    return best


def deskew(gray: np.ndarray) -> tuple[np.ndarray, float]:
    """Straighten a grayscale page. Returns (image, correction_degrees_applied)."""
    correction = estimate_tilt(gray)
    if abs(correction) < MIN_TILT_DEGREES:
        return gray, 0.0
    return _rotate(gray, correction, fill=255), round(correction, 2)