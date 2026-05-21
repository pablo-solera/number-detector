from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DetectionResult:
    """Result of scanning a single image."""

    image_name: str  # WITHOUT extension
    part_numbers: list[int]
    motor_codes: list[str]
    error: Optional[str] = None