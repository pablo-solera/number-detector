from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DetectionSettings:
    """All detection settings that can be tweaked from the GUI."""

    # HSV thresholds (UI sliders)
    s_min: int = 150
    v_min: int = 150

    # OCR parsing constraints for part numbers
    min_part_digits: int = 3
    max_part_digits: int = 6

    # Parallelism
    workers: int = 10

    # RGB red dominance (helps with washed-out reds / compression)
    red_rgb_delta: int = 35
    red_rgb_r_min: int = 110

    # Morphology for part callouts
    text_dilate_kernel: tuple[int, int] = (3, 3)
    text_dilate_iters: int = 1

    # Callout bbox filtering (avoid big red text blocks)
    part_min_h: int = 18
    part_max_w: int = 120
    part_max_h: int = 70

    # Motor search
    motor_region_pct: float = 0.90
    motor_dilate_kernel: tuple[int, int] = (3, 3)
    motor_dilate_iters: int = 1
