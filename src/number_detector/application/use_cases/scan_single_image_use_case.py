from __future__ import annotations

from pathlib import Path

from number_detector.application.ports import ImageReader, OcrReader, RedRegionDetector
from number_detector.application.settings import DetectionSettings
from number_detector.domain.models.detection_result import DetectionResult
from number_detector.domain.parsing import extract_free_texts, extract_motor_codes, extract_part_numbers


class ScanSingleImageUseCase:
    """Scan a single image and return detected red part numbers + motor codes."""

    def __init__(
        self,
        image_reader: ImageReader,
        detector: RedRegionDetector,
        ocr: OcrReader,
        settings: DetectionSettings | None = None,
    ):
        self.image_reader = image_reader
        self.detector = detector
        self.ocr = ocr
        self.settings = settings or DetectionSettings()

    def execute(self, image_path: str | Path) -> DetectionResult:
        p = Path(image_path)
        img = self.image_reader.read(p)
        if img is None:
            return DetectionResult(
                image_name=p.stem,
                part_numbers=[],
                motor_codes=[],
                free_text=[],
                body_text=[],
                error="No se pudo abrir",
            )

        parts: list[int] = []
        for region in self.detector.find_part_regions(img, name=p.stem):
            txt = self.ocr.read_digits(region.image)
            parts.extend(
                extract_part_numbers(
                    txt,
                    min_digits=self.settings.min_part_digits,
                    max_digits=self.settings.max_part_digits,
                )
            )

        motors: list[str] = []
        for region in self.detector.find_motor_regions(img, name=p.stem):
            txt = self.ocr.read_text(region.image)
            motors.extend(extract_motor_codes(txt))

        free_text: list[str] = []
        for region in self.detector.find_free_text_regions(img, name=p.stem):
            txt = self.ocr.read_free_text(region.image)
            free_text.extend(extract_free_texts(txt))

        body_text: list[str] = []
        for region in self.detector.find_body_text_regions(img, name=p.stem):
            txt = self.ocr.read_body_text(region.image)
            body_text.extend(extract_free_texts(txt))

        return DetectionResult(
            image_name=p.stem,
            part_numbers=sorted(set(parts)),
            motor_codes=sorted(set(motors)),
            free_text=sorted(set(free_text)),
            body_text=sorted(set(body_text)),
            error=None,
        )
