from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from number_detector.domain.models.bounding_box import BoundingBox


@dataclass(frozen=True)
class ImageRegion:
    bbox: BoundingBox
    image: Any
