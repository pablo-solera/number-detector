from __future__ import annotations

from pathlib import Path

from number_detector.application.ports import ResultsExporter
from number_detector.domain.models.detection_result import DetectionResult


class ExportExcelUseCase:

    def __init__(self, exporter: ResultsExporter):
        self.exporter = exporter

    def execute(self, results: list[DetectionResult], output_path: str | Path) -> Path:
        rows = []
        for r in results:
            if r.error:
                continue
            if r.part_numbers:
                for n in r.part_numbers:
                    rows.append([r.image_name, n, "".join(r.motor_codes) if r.motor_codes else ""])
            else:
                # still export motor if no numbers
                if r.motor_codes:
                    rows.append([r.image_name, "", "".join(r.motor_codes)])

        self.exporter.export(rows, output_path)
        return Path(output_path)
