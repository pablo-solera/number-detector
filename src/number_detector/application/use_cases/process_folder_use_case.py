from __future__ import annotations

from pathlib import Path
from typing import Optional, Callable

from number_detector.application.settings import DetectionSettings
from .export_excel_use_case import ExportExcelUseCase
from .scan_batch_images_use_case import ScanImagesBatchUseCase
from ...domain.models.detection_result import DetectionResult
from ...infrastructure.runtime import DEFAULT_OUTPUT_FILENAME

ProgressCallback = Callable[[int, int, str], None]
ResultCallback = Callable[[DetectionResult, int, int, str], None]


class ProcessFolderUseCase:
    """Scan a folder and automatically export an Excel to the output folder."""

    def __init__(self, settings: DetectionSettings, debug: bool = False, debug_dir: str | None = None):
        self.settings = settings
        self.debug = debug
        self.debug_dir = debug_dir

    def execute(
        self,
        input_dir: str | Path,
        output_dir: str | Path,
        on_progress: Optional[ProgressCallback] = None,
        on_result: Optional[ResultCallback] = None,
    ) -> tuple[list[DetectionResult], Path]:
        scan_uc = ScanImagesBatchUseCase(settings=self.settings, debug=self.debug, debug_dir=self.debug_dir)
        results = scan_uc.execute(input_dir=input_dir, on_progress=on_progress, on_result=on_result)

        output_dir_p = Path(output_dir)
        excel_path = output_dir_p / DEFAULT_OUTPUT_FILENAME

        ExportExcelUseCase().execute(results=results, output_path=excel_path)
        return results, excel_path
