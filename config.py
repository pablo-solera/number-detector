import os
from pathlib import Path

# Directorios del proyecto
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

# Crear directorios si no existen
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Configuración de Tesseract (descomentar y ajustar según OS)
# Windows
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Linux/Mac
# TESSERACT_CMD = None  # Usa el PATH del sistema

# Configuración de detección de color rojo (HSV)
RED_LOWER_1 = [0, 100, 100]
RED_UPPER_1 = [10, 255, 255]
RED_LOWER_2 = [170, 100, 100]
RED_UPPER_2 = [180, 255, 255]

# Configuración de filtrado de contornos
MIN_CONTOUR_WIDTH = 20
MIN_CONTOUR_HEIGHT = 20
CONTOUR_PADDING = 5

# Configuración de OCR
MIN_DIGITS = 2
TESSERACT_CONFIG = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'

# Extensiones de imagen soportadas
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

# Nombre del archivo de salida
OUTPUT_FILENAME = 'numeros_rojos.xlsx'
