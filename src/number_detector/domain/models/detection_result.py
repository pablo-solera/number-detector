from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class DetectionResult:
    """Result of scanning a single image."""

    image_name: str  # WITHOUT extension
    part_numbers: list[int]
    motor_codes: list[str]
    free_text: list[str] = field(default_factory=list)
    body_text: list[str] = field(default_factory=list)
    error: Optional[str] = None
