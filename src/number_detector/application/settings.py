from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DetectionSettings:
    """All detection settings that can be tweaked from the GUI."""

    # HSV thresholds (UI sliders)
    s_min: int = 150
    v_min: int = 150

    # OCR parsing constraints for part numbers
    min_part_digits: int = 2
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
    part_merge_gap: int = 8
    part_roi_padding: int = 2

    # Motor search
    motor_region_pct: float = 0.90
    motor_min_y_pct: float = 0.18
    motor_blue_h_min: int = 90
    motor_blue_h_max: int = 145
    motor_blue_s_min: int = 40
    motor_blue_v_min: int = 40
    motor_dilate_kernel: tuple[int, int] = (9, 5)
    motor_dilate_iters: int = 2
    motor_min_w: int = 60
    motor_min_h: int = 20
    motor_max_w: int = 350
    motor_max_h: int = 140
    motor_min_area: int = 250
    motor_roi_padding: int = 8

    # Free text search (green labels)
    free_text_green_h_min: int = 35
    free_text_green_h_max: int = 90
    free_text_green_s_min: int = 40
    free_text_green_v_min: int = 40
    free_text_min_y_pct: float = 0.18
    free_text_max_x_pct: float = 0.58
    free_text_dilate_kernel: tuple[int, int] = (9, 5)
    free_text_dilate_iters: int = 2
    free_text_min_w: int = 60
    free_text_min_h: int = 15
    free_text_max_w: int = 500
    free_text_max_h: int = 180
    free_text_min_area: int = 150
    free_text_roi_padding: int = 8
