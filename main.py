"""
Punto de entrada de la aplicacion
Detector de Numeros Rojos
"""
from multiprocessing import freeze_support
from src.ui import main

# Comprobación de Tesseract
from src.check_tesseract import check_tesseract_installed

check_tesseract_installed()

if __name__ == "__main__":
    freeze_support()
    main()
