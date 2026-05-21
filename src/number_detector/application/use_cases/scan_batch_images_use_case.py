from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Optional

from number_detector.application.settings import DetectionSettings
from number_detector.application.use_cases.list_images_use_case import ListImagesUseCase
from number_detector.domain.models.detection_result import DetectionResult

ProgressCallback = Callable[[int, int, str], None]
ResultCallback = Callable[[DetectionResult, int, int, str], None]
ScanOne = Callable[[str, dict, bool, str | None], DetectionResult]


class ScanImagesBatchUseCase:
    """Use case: scan many images using ProcessPoolExecutor (max performance)."""

    def __init__(
        self,
        settings: DetectionSettings,
        scan_one: ScanOne,
        debug: bool = False,
        debug_dir: str | None = None,
    ):
        self.settings = settings
        self.scan_one = scan_one
        self.debug = debug
        self.debug_dir = debug_dir

    def execute(
        self,
        input_dir: str | Path,
        on_progress: Optional[ProgressCallback] = None,
        on_result: Optional[ResultCallback] = None,
    ) -> list[DetectionResult]:

        images = ListImagesUseCase().execute(input_dir).images
        if not images:
            return []

        settings_dict = asdict(self.settings)
        total = len(images)

        # Pre-fill preserving original order
        results: list[DetectionResult] = [
            DetectionResult(image_name=p.stem, part_numbers=[], motor_codes=[], error="pending")
            for p in images
        ]

        with ProcessPoolExecutor(max_workers=max(1, self.settings.workers)) as ex:
            fut_to_idx = {
                ex.submit(self.scan_one, str(img_path), settings_dict, self.debug, self.debug_dir): idx
                for idx, img_path in enumerate(images)
            }

            done = 0
            for fut in as_completed(fut_to_idx):
                idx = fut_to_idx[fut]
                p = images[idx]

                try:
                    results[idx] = fut.result()
                except Exception as e:
                    results[idx] = DetectionResult(
                        image_name=p.stem,
                        part_numbers=[],
                        motor_codes=[],
                        error=f"{type(e).__name__}: {e}",
                    )

                done += 1
                if on_result:
                    on_result(results[idx], done, total, p.name)
                if on_progress:
                    on_progress(done, total, p.name)

        return results
