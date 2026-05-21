from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QFileDialog


class FolderDropWidget(QLabel):
    """
    Área de drag&drop de carpetas + click para abrir selector.
    Emite path_changed(Path) cuando cambia.
    """
    path_changed = Signal(object)  # Path

    def __init__(self, title: str, placeholder: str = "Suelta una carpeta aquí o haz click para seleccionar"):
        super().__init__()
        self._title = title
        self._path: Path | None = None

        self.setAcceptDrops(True)
        self.setMinimumHeight(64)
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.setWordWrap(True)

        self._placeholder = placeholder
        self._apply_style(idle=True)
        self._render()

    def path(self) -> Path | None:
        return self._path

    def set_path(self, p: str | Path | None):
        if not p:
            self._path = None
            self._render()
            return
        pp = Path(p)
        if not pp.exists() or not pp.is_dir():
            return
        self._path = pp
        self._render()
        self.path_changed.emit(self._path)

    # ---- Qt events ----
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            chosen = QFileDialog.getExistingDirectory(self, f"Selecciona carpeta ({self._title})")
            if chosen:
                self.set_path(chosen)
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Aceptamos si hay al menos una carpeta
            for url in event.mimeData().urls():
                p = Path(url.toLocalFile())
                if p.exists() and p.is_dir():
                    event.acceptProposedAction()
                    self._apply_style(idle=False)
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._apply_style(idle=True)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._apply_style(idle=True)
        urls = event.mimeData().urls()
        if not urls:
            return

        # Prioriza el primer directorio válido
        for url in urls:
            p = Path(url.toLocalFile())
            if p.exists() and p.is_dir():
                self.set_path(p)
                event.acceptProposedAction()
                return

    # ---- UI ----
    def _render(self):
        if self._path:
            self.setText(f"<b>{self._title}:</b><br>{self._path}")
        else:
            self.setText(f"<b>{self._title}:</b><br><span style='color:#666'>{self._placeholder}</span>")

    def _apply_style(self, idle: bool):
        if idle:
            self.setStyleSheet(
                "QLabel {"
                " border: 2px dashed #9aa0a6;"
                " border-radius: 12px;"
                " padding: 10px 12px;"
                "}"
            )
        else:
            self.setStyleSheet(
                "QLabel {"
                " border: 2px dashed #2e7d32;"
                " border-radius: 12px;"
                " padding: 10px 12px;"
                "}"
            )
