from __future__ import annotations

import os
from pathlib import Path


IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
DEFAULT_OUTPUT_FILENAME = "numeros_rojos.xlsx"


# Tesseract path (override with env var TESSERACT_CMD)
TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)


def default_output_dir() -> Path:
    """A sensible default for output files."""
    return Path.cwd()


def check_tesseract_installed() -> bool:
    """Basic check that Tesseract is callable. Returns True/False."""
    try:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False
