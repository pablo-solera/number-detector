from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from number_detector.domain.models.detection_result import DetectionResult
from number_detector.infrastructure.excel_exporter import ExcelExporter


class ExportExcelUseCase:

    def __init__(self):
        #self.exporter = ExcelExporter()
        pass

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

        ExcelExporter(str(output_path)).export(rows)
        return Path(output_path)
