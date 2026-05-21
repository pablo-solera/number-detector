from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from number_detector.domain.models.image_region import ImageRegion


Image = Any


class ImageReader(Protocol):
    def read(self, image_path: str | Path) -> Image | None:
        """Read an image from disk or return None when it cannot be opened."""


class OcrReader(Protocol):
    def read_digits(self, image: Image) -> str:
        """Read numeric text from an image region."""

    def read_text(self, image: Image) -> str:
        """Read free-form motor text from an image region."""


class RedRegionDetector(Protocol):
    def find_part_regions(self, image: Image, name: str = "") -> list[ImageRegion]:
        """Find red part-number regions to OCR."""

    def find_motor_regions(self, image: Image, name: str = "") -> list[ImageRegion]:
        """Find red motor-code regions to OCR."""


class ResultsExporter(Protocol):
    def export(self, rows: list[list[object]], output_path: str | Path) -> Path:
        """Persist exported result rows and return the destination path."""
