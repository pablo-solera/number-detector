"""
Punto de entrada de la aplicacion
Detector de Numeros Rojos
"""
import sys
from pathlib import Path
from src.ui import main

# Agregar directorio raiz al path
sys.path.insert(0, str(Path(__file__).parent))

# Comprobación de Tesseract
from src.check_tesseract import check_tesseract_installed
check_tesseract_installed()


if __name__ == "__main__":
    main()