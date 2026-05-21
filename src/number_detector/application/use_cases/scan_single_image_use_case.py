from __future__ import annotations

from pathlib import Path

import cv2

from number_detector.application.settings import DetectionSettings
from number_detector.domain.models.detection_result import DetectionResult
from number_detector.domain.parsing import extract_motor_codes, extract_part_numbers
from number_detector.infrastructure.imaging import OpenCVRedDetector
from number_detector.infrastructure.ocr import TesseractService
from number_detector.infrastructure.runtime import TESSERACT_CMD


class ScanSingleImageUseCase:
    """Scan a single image and return detected red part numbers + motor codes."""

    def __init__(self, settings: DetectionSettings = DetectionSettings, debug: bool = False,
                 debug_dir: str | None = None):
        self.settings = DetectionSettings
        self.debug = debug
        self.debug_dir = debug_dir

        self.detector = OpenCVRedDetector(settings=settings, debug=debug, debug_dir=debug_dir)
        self.ocr = TesseractService(tesseract_cmd=TESSERACT_CMD)

    def execute(self, image_path: str | Path) -> DetectionResult:
        p = Path(image_path)
        img = cv2.imread(str(p))
        if img is None:
            return DetectionResult(image_name=p.stem, part_numbers=[], motor_codes=[], error="No se pudo abrir")

        parts: list[int] = []
        for bb in self.detector.find_part_bboxes(img, name=p.stem):
            roi = img[bb.y: bb.y + bb.h, bb.x: bb.x + bb.w]
            txt = self.ocr.read_digits(roi)
            parts.extend(extract_part_numbers(txt))

        parts: list[int] = []
        for bb in self.detector.find_part_bboxes(img, name=p.stem):
            roi = img[bb.y: bb.y + bb.h, bb.x: bb.x + bb.w]
            txt = self.ocr.read_digits(roi)
            parts.extend(extract_part_numbers(txt))

        motors: list[str] = []
        for _bb, roi in self.detector.find_motor_bboxes(img, name=p.stem):
            txt = self.ocr.read_text(roi)
            motors.extend(extract_motor_codes(txt))

        return DetectionResult(
            image_name=p.stem,
            part_numbers=sorted(set(parts)),
            motor_codes=sorted(set(motors)),
            error=None,
        )
