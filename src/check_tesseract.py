import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from config import TESSERACT_CMD


def check_tesseract_installed():
    """
    Comprueba si Tesseract está instalado en el equipo.
    Muestra un dialogo de error si no se encuentra y termina la ejecución.
    """
    tesseract_path = Path(TESSERACT_CMD)

    if not tesseract_path.is_file():
        # Inicializar root temporal para messagebox
        root = tk.Tk()
        root.withdraw()  # Oculta la ventana principal

        messagebox.showerror(
            "Tesseract no encontrado",
            f"Tesseract OCR no está instalado o no se encuentra en la ruta configurada:\n\n{tesseract_path}\n\n"
            "Instala Tesseract desde: https://github.com/tesseract-ocr/tesseract"
        )
        root.destroy()
        sys.exit(1)
