from __future__ import annotations

from pathlib import Path
from typing import Optional, Callable

from number_detector.application.settings import DetectionSettings
from number_detector.application.constants import DEFAULT_OUTPUT_FILENAME
from .export_excel_use_case import ExportExcelUseCase
from .scan_batch_images_use_case import ScanImagesBatchUseCase
from ...domain.models.detection_result import DetectionResult

ProgressCallback = Callable[[int, int, str], None]
ResultCallback = Callable[[DetectionResult, int, int, str], None]


class ProcessFolderUseCase:
    """Scan a folder and automatically export an Excel to the output folder."""

    def __init__(
        self,
        settings: DetectionSettings,
        scan_uc: ScanImagesBatchUseCase,
        export_uc: ExportExcelUseCase,
    ):
        self.settings = settings
        self.scan_uc = scan_uc
        self.export_uc = export_uc

    def execute(
        self,
        input_dir: str | Path,
        output_dir: str | Path,
        on_progress: Optional[ProgressCallback] = None,
        on_result: Optional[ResultCallback] = None,
    ) -> tuple[list[DetectionResult], Path]:
        results = self.scan_uc.execute(input_dir=input_dir, on_progress=on_progress, on_result=on_result)

        output_dir_p = Path(output_dir)
        excel_path = output_dir_p / DEFAULT_OUTPUT_FILENAME

        self.export_uc.execute(results=results, output_path=excel_path)
        return results, excel_path
