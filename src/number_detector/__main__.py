from __future__ import annotations

from multiprocessing import freeze_support

from number_detector.presentation.pyside_app.main import run_pyside6_ui

if __name__ == "__main__":
    freeze_support()
    run_pyside6_ui()
