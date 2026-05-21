from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ListImagesResult:
    images: list[Path]