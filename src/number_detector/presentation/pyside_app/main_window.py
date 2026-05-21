from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QHBoxLayout, QProgressBar, QPlainTextEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
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
        self.setWindowTitle("Detector ETKA")
        self.resize(1100, 740)

        self.worker: FolderScanWorker | None = None
        self.last_excel_path: Path | None = None

        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet("background: #f7f8fd;")
        main = QVBoxLayout(root)
        main.setContentsMargins(18, 14, 18, 14)
        main.setSpacing(16)

        # ---- Carpetas ----
        paths_panel = QFrame()
        paths_panel.setStyleSheet("QFrame { background: transparent; border: none; }")
        main.addWidget(paths_panel)
        grid = QGridLayout(paths_panel)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.in_drop = FolderDropWidget("Carpeta de entrada", "Suelta una carpeta o haz click para seleccionar")
        self.out_drop = FolderDropWidget("Carpeta de salida", "Selecciona dónde guardar el Excel")

        self.lbl_found = QLabel("0 imágenes encontradas")
        self.lbl_found.setStyleSheet("color: #4d5f7a; font-size: 12px;")

        grid.addWidget(self.in_drop, 0, 0)
        grid.addWidget(self.out_drop, 0, 1)
        grid.addWidget(self.lbl_found, 1, 0, 1, 2)

        self.in_drop.path_changed.connect(self._update_found_count)

        self.btn_run = QPushButton("PROCESAR IMÁGENES")
        self.btn_run.setMinimumHeight(42)
        self.btn_run.setStyleSheet(
            "QPushButton { background:#0047a8; color:white; border:none; padding:0 18px; font-weight:700; }"
            "QPushButton:disabled { background:#9eb6da; }"
        )

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setMinimumHeight(42)
        self.btn_cancel.setStyleSheet(
            "QPushButton { background:#ffffff; color:#001b44; border:1px solid #cfd8ea; padding:0 18px; }"
            "QPushButton:disabled { color:#9aa6bd; background:#f7f8fd; }"
        )

        self.btn_open_excel = QPushButton("Abrir Excel")
        self.btn_open_excel.setEnabled(False)
        self.btn_open_excel.setMinimumHeight(42)
        self.btn_open_excel.setStyleSheet(
            "QPushButton { background:#ffffff; color:#001b44; border:1px solid #cfd8ea; padding:0 18px; }"
            "QPushButton:disabled { color:#aab3c2; background:#f7f8fd; }"
        )
        self.btn_open_excel.clicked.connect(self.open_excel)

        self.btn_run.clicked.connect(self.start_processing)
        self.btn_cancel.clicked.connect(self.cancel_processing)

        # ---- Progreso ----
        g_prog = QGroupBox("Escaneo")
        main.addWidget(g_prog)
        prog = QVBoxLayout(g_prog)
        prog.setContentsMargins(18, 16, 18, 16)
        g_prog.setStyleSheet(
            "QGroupBox { background:#ffffff; border:1px solid #cfd8ea; margin-top:8px; font-weight:700; color:#001b44; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }"
        )

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setTextVisible(False)
        self.progress.setMinimumHeight(8)
        self.progress.setStyleSheet(
            "QProgressBar { background:#dbe7ff; border:none; border-radius:4px; }"
            "QProgressBar::chunk { background:#0047a8; border-radius:4px; }"
        )

        progress_header = QHBoxLayout()
        self.lbl_progress_title = QLabel("Listo para escanear")
        self.lbl_progress_title.setStyleSheet("font-size:15px; font-weight:700; color:#001b44;")
        self.lbl_progress_pct = QLabel("0%")
        self.lbl_progress_pct.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_progress_pct.setStyleSheet("font-size:12px; color:#0047a8; font-weight:700;")
        progress_header.addWidget(self.lbl_progress_title)
        progress_header.addStretch(1)
        progress_header.addWidget(self.lbl_progress_pct)

        self.lbl_progress = QLabel("Selecciona carpetas para empezar")
        self.lbl_progress.setStyleSheet("color:#4d5f7a; font-size:12px;")
        prog.addLayout(progress_header)
        prog.addWidget(self.progress)
        prog.addWidget(self.lbl_progress)

        # ---- Resultados ----
        g_res = QGroupBox("Resultados")
        main.addWidget(g_res, 2)
        res_layout = QVBoxLayout(g_res)
        res_layout.setContentsMargins(0, 10, 0, 0)
        g_res.setStyleSheet(
            "QGroupBox { background:#ffffff; border:1px solid #cfd8ea; margin-top:8px; font-weight:700; color:#001b44; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }"
        )

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Imagen", "Números", "Motores", "Carrocería", "Free text", "Error"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(
            "QTableWidget { border:none; background:#ffffff; alternate-background-color:#f1f5fb; color:#001b44; }"
            "QHeaderView::section { background:#eef2fc; color:#5b6578; border:none; border-bottom:1px solid #cfd8ea; padding:9px; font-weight:700; }"
            "QTableWidget::item { border-bottom:1px solid #e5ebf5; padding:8px; }"
            "QTableWidget::item:selected { background:#dbeafe; color:#001b44; }"
            "QTableWidget::item:focus { outline:none; }"
        )
        res_layout.addWidget(self.table)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)

        # ---- Acciones ----
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        main.addLayout(action_row)
        action_row.addStretch(1)
        action_row.addWidget(self.btn_run)
        action_row.addWidget(self.btn_cancel)
        action_row.addWidget(self.btn_open_excel)

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
            self.lbl_found.setText("0 imágenes encontradas")
            return

        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
        count = sum(1 for f in p.iterdir() if f.is_file() and f.suffix.lower() in exts)
        self.lbl_found.setText(f"{count} imágenes encontradas")

    def append_log(self, text: str):
        self.log.appendPlainText(text)

    # ---------- Excel ----------
    @Slot()
    def open_excel(self):
        if not self.last_excel_path:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_excel_path)))

    # ---------- Table ----------
    @Slot(str, str, str, str, str, str)
    def on_result(
        self,
        image_name: str,
        parts_csv: str,
        motors_csv: str,
        body_text_csv: str,
        free_text_csv: str,
        error: str,
    ):
        # Append row as results arrive (completion order may differ from file order)
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(image_name))
        self.table.setItem(r, 1, QTableWidgetItem(parts_csv))
        self.table.setItem(r, 2, QTableWidgetItem(motors_csv))
        self.table.setItem(r, 3, QTableWidgetItem(body_text_csv))
        self.table.setItem(r, 4, QTableWidgetItem(free_text_csv))
        self.table.setItem(r, 5, QTableWidgetItem(error))

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

        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)

        self.progress.setRange(0, len(images))
        self.progress.setValue(0)
        self.lbl_progress_pct.setText("0%")
        self.lbl_progress_title.setText("Escaneando imágenes...")
        self.lbl_progress.setText(f"Preparando {len(images)} imágenes...")
        self.append_log(f"Procesando {len(images)} imágenes. El Excel se exportará al terminar.")

        self.worker = FolderScanWorker(input_dir=in_dir, output_dir=out_dir, debug=False)
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
            self.lbl_progress_title.setText("Cancelando...")
            self.lbl_progress.setText("Cancelando proceso...")
            self.append_log("Cancelación solicitada...")

    @Slot(int)
    def on_started(self, total: int):
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(0)
        self.lbl_progress_pct.setText("0%")
        self.lbl_progress_title.setText("Escaneando imágenes...")
        self.lbl_progress.setText(f"Preparando {total} imágenes...")

    @Slot(int, int, str)
    def on_progress(self, done: int, total: int, filename: str):
        self.progress.setValue(done)
        pct = int((done / max(total, 1)) * 100)
        self.lbl_progress_pct.setText(f"{pct}%")
        self.lbl_progress.setText(f"Procesando imagen {done} de {total} · {filename}")

    @Slot(str)
    def on_finished(self, excel_path: str):
        if excel_path:
            self.last_excel_path = Path(excel_path)
            self.btn_open_excel.setEnabled(True)
            self.lbl_progress_title.setText("Escaneo completado")
            self.lbl_progress_pct.setText("100%")
            self.lbl_progress.setText("Proceso completado · Excel listo")
            QMessageBox.information(self, "Terminado", f"Proceso completado.\nExcel exportado en:\n{excel_path}")
        else:
            self.lbl_progress_title.setText("Escaneo cancelado")
            self.lbl_progress.setText("Proceso cancelado")
            QMessageBox.information(self, "Cancelado", "Proceso cancelado.")

        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.worker = None

    @Slot(str)
    def on_error(self, msg: str):
        self.append_log(f"❌ Error: {msg}")
        QMessageBox.critical(self, "Error", msg)
        self.lbl_progress_title.setText("Error")
        self.lbl_progress.setText("No se pudo completar el proceso")
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.worker = None
