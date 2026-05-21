from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from number_detector.domain.models.list_images_result import ListImagesResult

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}



class ListImagesUseCase:
    """List images in a folder (non-recursive)."""

    def execute(self, input_dir: str | Path) -> ListImagesResult:
        p = Path(input_dir)
        if not p.exists() or not p.is_dir():
            return ListImagesResult(images=[])

        images = [
            f for f in p.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        images.sort(key=lambda x: x.name.lower())
        return ListImagesResult(images=images)
