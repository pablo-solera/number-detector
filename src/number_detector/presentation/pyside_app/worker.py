from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from number_detector.application.settings import DetectionSettings
from number_detector.application.use_cases.list_images_use_case import ListImagesUseCase
from number_detector.application.use_cases.process_folder_use_case import ProcessFolderUseCase
from number_detector.domain.models.detection_result import DetectionResult


class FolderScanWorker(QThread):
    sig_started = Signal(int)  # total
    sig_progress = Signal(int, int, str)  # done, total, filename
    sig_result = Signal(str, str, str, str)  # image_name, parts_csv, motors_csv, error
    sig_log = Signal(str)
    sig_finished = Signal(str)  # excel path
    sig_error = Signal(str)

    def __init__(self, input_dir: Path, output_dir: Path, s_min: int, v_min: int, debug: bool = False):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.s_min = s_min
        self.v_min = v_min
        self.debug = debug
        self._cancel = False

    def request_cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            settings = DetectionSettings(s_min=self.s_min, v_min=self.v_min)

            uc = ProcessFolderUseCase(
                settings=settings,
                debug=self.debug,
                debug_dir=str(self.output_dir / "_debug") if self.debug else None,
            )

            # Pre-count images quickly (non-recursive)

            images = ListImagesUseCase().execute(self.input_dir).images
            total = len(images)
            self.sig_started.emit(total)

            def on_progress(done: int, total_: int, filename: str) -> None:
                if self._cancel:
                    raise RuntimeError("CANCELLED")
                self.sig_progress.emit(done, total_, filename)

            def on_log(msg: str):
                self.sig_log.emit(msg)

            def on_result(res: DetectionResult, done: int, total_: int, filename: str) -> None:
                # Update UI table incrementally
                parts_csv = ",".join(str(x) for x in res.part_numbers)
                motors_csv = ",".join(res.motor_codes)
                err = res.error or ""
                self.sig_result.emit(res.image_name, parts_csv, motors_csv, err)

            _results, excel_path = uc.execute(
                input_dir=self.input_dir,
                output_dir=self.output_dir,
                on_progress=on_progress,
                on_result=on_result,
            )

            self.sig_finished.emit(str(excel_path))

        except RuntimeError as e:
            if str(e) == "CANCELLED":
                self.sig_log.emit("⛔ Cancelado por el usuario.")
                self.sig_finished.emit("")  # no excel
            else:
                self.sig_error.emit(str(e))
        except Exception as e:
            self.sig_error.emit(f"{type(e).__name__}: {e}")
