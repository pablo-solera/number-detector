from __future__ import annotations

from pathlib import Path

from number_detector.application.settings import DetectionSettings
from number_detector.application.use_cases.export_excel_use_case import ExportExcelUseCase
from number_detector.application.use_cases.process_folder_use_case import ProcessFolderUseCase
from number_detector.application.use_cases.scan_batch_images_use_case import ScanImagesBatchUseCase
from number_detector.application.use_cases.scan_single_image_use_case import ScanSingleImageUseCase
from number_detector.domain.models.detection_result import DetectionResult
from number_detector.infrastructure.excel_exporter import ExcelExporter
from number_detector.infrastructure.imaging import OpenCVImageReader, OpenCVRedDetector
from number_detector.infrastructure.ocr import TesseractService
from number_detector.infrastructure.runtime import TESSERACT_CMD


def create_scan_single_image_use_case(
    settings: DetectionSettings,
    debug: bool = False,
    debug_dir: str | None = None,
) -> ScanSingleImageUseCase:
    return ScanSingleImageUseCase(
        image_reader=OpenCVImageReader(),
        detector=OpenCVRedDetector(settings=settings, debug=debug, debug_dir=debug_dir),
        ocr=TesseractService(tesseract_cmd=TESSERACT_CMD),
        settings=settings,
    )


def scan_one_image(
    image_path: str,
    settings_dict: dict,
    debug: bool,
    debug_dir: str | None,
) -> DetectionResult:
    settings = DetectionSettings(**settings_dict)
    return create_scan_single_image_use_case(settings=settings, debug=debug, debug_dir=debug_dir).execute(image_path)


def create_process_folder_use_case(
    settings: DetectionSettings,
    debug: bool = False,
    debug_dir: str | None = None,
) -> ProcessFolderUseCase:
    scan_uc = ScanImagesBatchUseCase(
        settings=settings,
        scan_one=scan_one_image,
        debug=debug,
        debug_dir=debug_dir,
    )
    export_uc = ExportExcelUseCase(exporter=ExcelExporter())
    return ProcessFolderUseCase(settings=settings, scan_uc=scan_uc, export_uc=export_uc)
