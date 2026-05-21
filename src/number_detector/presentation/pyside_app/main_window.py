from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog, QSlider,
    QHBoxLayout, QProgressBar, QPlainTextEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)

from number_detector.application.use_cases.list_images_use_case import ListImagesUseCase
from .widgets.folder_dnd_widget import FolderDropWidget
from .worker import FolderScanWorker


class DropDirLineEdit(QLineEdit):
    """Line edit that accepts folder drag&drop."""

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        p = Path(urls[0].toLocalFile())
        if p.exists() and p.is_dir():
            self.setText(str(p))
        event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detector de Números Rojos")
        self.resize(980, 780)

        self.worker: FolderScanWorker | None = None
        self.last_excel_path: Path | None = None

        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setSpacing(12)

        title = QLabel("Detector de Números Rojos")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #1e66d0;")
        main.addWidget(title)

        # ---- Grupo: Carpetas ----
        g_paths = QGroupBox("Carpetas")
        main.addWidget(g_paths)
        grid = QGridLayout(g_paths)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.in_drop = FolderDropWidget("Carpeta de entrada")
        self.out_drop = FolderDropWidget("Carpeta de salida")

        self.lbl_found = QLabel("Imágenes encontradas: 0")

        grid.addWidget(self.in_drop, 0, 0, 1, 2)
        grid.addWidget(self.lbl_found, 1, 0, 1, 2)
        grid.addWidget(self.out_drop, 2, 0, 1, 2)

        self.in_drop.path_changed.connect(self._update_found_count)

        # ---- Config detección ----
        g_cfg = QGroupBox("Configuración de Detección")
        main.addWidget(g_cfg)
        cfg = QGridLayout(g_cfg)
        cfg.setColumnStretch(1, 1)

        self.s_slider = QSlider(Qt.Orientation.Horizontal)
        self.s_slider.setRange(0, 255)
        self.s_slider.setValue(150)

        self.v_slider = QSlider(Qt.Orientation.Horizontal)
        self.v_slider.setRange(0, 255)
        self.v_slider.setValue(150)

        self.lbl_s = QLabel("150")
        self.lbl_v = QLabel("150")
        self.lbl_level = QLabel("")
        self.lbl_level.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        cfg.addWidget(QLabel("Saturación mínima (S):"), 0, 0)
        cfg.addWidget(self.s_slider, 0, 1)
        cfg.addWidget(self.lbl_s, 0, 2)

        cfg.addWidget(QLabel("Brillo mínimo (V):"), 1, 0)
        cfg.addWidget(self.v_slider, 1, 1)
        cfg.addWidget(self.lbl_v, 1, 2)

        cfg.addWidget(self.lbl_level, 2, 0, 1, 3)

        preset_row = QHBoxLayout()
        cfg.addLayout(preset_row, 3, 0, 1, 3)

        preset_row.addWidget(QLabel("Presets:"))
        for label, s, v in [
            ("Muy Permisivo", 60, 60),
            ("Permisivo", 90, 90),
            ("Medio", 120, 120),
            ("Restrictivo", 150, 150),
            ("Muy Restrictivo", 180, 180),
        ]:
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, ss=s, vv=v: self._apply_preset(ss, vv))
            preset_row.addWidget(b)
        preset_row.addStretch(1)

        self.s_slider.valueChanged.connect(self._sync_labels)
        self.v_slider.valueChanged.connect(self._sync_labels)
        self._sync_labels()

        # ---- Acciones ----
        action_row = QHBoxLayout()
        main.addLayout(action_row)

        self.btn_run = QPushButton("PROCESAR IMÁGENES")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.setStyleSheet("font-weight: 700;")

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setEnabled(False)

        self.btn_open_excel = QPushButton("Abrir Excel")
        self.btn_open_excel.setEnabled(False)
        self.btn_open_excel.clicked.connect(self.open_excel)

        action_row.addStretch(1)
        action_row.addWidget(self.btn_run)
        action_row.addWidget(self.btn_cancel)
        action_row.addWidget(self.btn_open_excel)
        action_row.addStretch(1)

        self.btn_run.clicked.connect(self.start_processing)
        self.btn_cancel.clicked.connect(self.cancel_processing)

        # ---- Progreso ----
        g_prog = QGroupBox("Progreso")
        main.addWidget(g_prog)
        prog = QVBoxLayout(g_prog)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.lbl_progress = QLabel("Listo para procesar")
        prog.addWidget(self.progress)
        prog.addWidget(self.lbl_progress)

        # ---- Resultados ----
        g_res = QGroupBox("Resultados")
        main.addWidget(g_res, 2)
        res_layout = QVBoxLayout(g_res)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Imagen", "Números", "Motores", "Free text", "Error"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        res_layout.addWidget(self.table)

        # ---- Log ----
        g_log = QGroupBox("Log")
        main.addWidget(g_log, 1)
        log_layout = QVBoxLayout(g_log)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        log_layout.addWidget(self.log)

    # ---------- UI helpers ----------
    def _apply_preset(self, s: int, v: int):
        self.s_slider.setValue(s)
        self.v_slider.setValue(v)

    def _sync_labels(self):
        s = self.s_slider.value()
        v = self.v_slider.value()
        self.lbl_s.setText(str(s))
        self.lbl_v.setText(str(v))

        if s <= 80 and v <= 80:
            level = "Muy Permisivo"
        elif s <= 110 and v <= 110:
            level = "Permisivo"
        elif s <= 140 and v <= 140:
            level = "Medio"
        elif s <= 170 and v <= 170:
            level = "Restrictivo"
        else:
            level = "Muy Restrictivo"

        self.lbl_level.setText(f"Nivel: {level}")

    @Slot()
    def pick_input_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Selecciona carpeta de entrada")
        if path:
            self.in_path.setText(path)

    @Slot()
    def pick_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Selecciona carpeta de salida")
        if path:
            self.out_path.setText(path)

    @Slot(object)
    def _update_found_count(self, *_):
        p = self.in_drop.path()
        if not p:
            self.lbl_found.setText("Imágenes encontradas: 0")
            return

        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
        count = sum(1 for f in p.iterdir() if f.is_file() and f.suffix.lower() in exts)
        self.lbl_found.setText(f"Imágenes encontradas: {count}")

    def append_log(self, text: str):
        self.log.appendPlainText(text)

    # ---------- Excel ----------
    @Slot()
    def open_excel(self):
        if not self.last_excel_path:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_excel_path)))

    # ---------- Table ----------
    @Slot(str, str, str, str, str)
    def on_result(self, image_name: str, parts_csv: str, motors_csv: str, free_text_csv: str, error: str):
        # Append row as results arrive (completion order may differ from file order)
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(image_name))
        self.table.setItem(r, 1, QTableWidgetItem(parts_csv))
        self.table.setItem(r, 2, QTableWidgetItem(motors_csv))
        self.table.setItem(r, 3, QTableWidgetItem(free_text_csv))
        self.table.setItem(r, 4, QTableWidgetItem(error))

    # ---------- Processing ----------
    @Slot()
    def start_processing(self):
        self.last_excel_path = None
        self.btn_open_excel.setEnabled(False)
        self.table.setRowCount(0)

        in_dir = self.in_drop.path()
        out_dir = self.out_drop.path()

        if not in_dir:
            QMessageBox.warning(self, "Entrada inválida", "Selecciona una carpeta de entrada válida.")
            return
        if not out_dir:
            QMessageBox.warning(self, "Salida inválida", "Selecciona una carpeta de salida válida.")
            return

        images = ListImagesUseCase().execute(in_dir).images
        if not images:
            QMessageBox.information(self, "Sin imágenes", "No se han encontrado imágenes en la carpeta de entrada.")
            return

        s_min = self.s_slider.value()
        v_min = self.v_slider.value()

        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)

        self.progress.setRange(0, len(images))
        self.progress.setValue(0)
        self.lbl_progress.setText(f"0/{len(images)}…")
        self.append_log(f"Procesando {len(images)} imágenes… (exportación automática al terminar)")

        self.worker = FolderScanWorker(input_dir=in_dir, output_dir=out_dir, s_min=s_min, v_min=v_min, debug=False)
        self.worker.sig_started.connect(self.on_started)
        self.worker.sig_progress.connect(self.on_progress)
        self.worker.sig_result.connect(self.on_result)
        self.worker.sig_log.connect(self.append_log)
        self.worker.sig_finished.connect(self.on_finished)
        self.worker.sig_error.connect(self.on_error)
        self.worker.start()

    @Slot()
    def cancel_processing(self):
        if self.worker:
            self.worker.request_cancel()
            self.btn_cancel.setEnabled(False)
            self.append_log("Cancelación solicitada…")

    @Slot(int)
    def on_started(self, total: int):
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(0)

    @Slot(int, int, str)
    def on_progress(self, done: int, total: int, filename: str):
        self.progress.setValue(done)
        self.lbl_progress.setText(f"Procesando {done}/{total}: {filename}")

    @Slot(str)
    def on_finished(self, excel_path: str):
        if excel_path:
            self.last_excel_path = Path(excel_path)
            self.btn_open_excel.setEnabled(True)
            self.append_log(f"✅ Excel exportado: {excel_path}")
            QMessageBox.information(self, "Terminado", f"Proceso completado.\nExcel exportado en:\n{excel_path}")
        else:
            self.append_log("⛔ Proceso cancelado.")

        self.lbl_progress.setText("Listo.")
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.worker = None

    @Slot(str)
    def on_error(self, msg: str):
        self.append_log(f"❌ Error: {msg}")
        QMessageBox.critical(self, "Error", msg)
        self.lbl_progress.setText("Error.")
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.worker = None
