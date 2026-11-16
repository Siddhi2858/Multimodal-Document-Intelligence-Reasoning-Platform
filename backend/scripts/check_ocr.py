"""
scripts/check_ocr.py
--------------------
Is OCR ready on this computer?  Finds Tesseract, prints its version, and reads a
small test image.

Usage (from the backend/ folder):
    python -m scripts.check_ocr
"""

from PIL import Image, ImageDraw, ImageFont

from ocr import engine

path = engine.find_tesseract()
print(f"Tesseract found at : {path or 'NOT FOUND'}")

if path is None:
    raise SystemExit("\n" + engine.INSTALL_HELP)

print(f"Tesseract version  : {engine.version()}")

font = None
for name in ("arial.ttf", "DejaVuSans.ttf"):
    try:
        font = ImageFont.truetype(name, 44)
        break
    except OSError:
        continue
if font is None:
    try:
        font = ImageFont.load_default(size=44)
    except TypeError:
        font = ImageFont.load_default()

image = Image.new("L", (900, 220), 255)
draw = ImageDraw.Draw(image)
draw.text((30, 25), "Folio OCR check 2026", fill=0, font=font)
draw.text((30, 110), "Page 4: accuracy 93.42%", fill=0, font=font)

result = engine.ocr_image(image, dpi=200)
print(f"OCR read           : {result['text']!r}   (confidence {result['avg_confidence']:.2f})")
print("\nOCR is ready." if "93.42" in result["text"] else "\nOCR ran but read the test image badly. Check the Tesseract installation.")