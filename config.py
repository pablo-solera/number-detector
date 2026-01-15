"""
Configuracion centralizada de la aplicacion
"""
from pathlib import Path

# ============================================================================
# RUTAS DEL PROYECTO
# ============================================================================
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
DEBUG_DIR = OUTPUT_DIR / "debug"
OUTPUT_FILENAME = "numeros_rojos.xlsx"

# Crear directorios si no existen
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# CONFIGURACION DE TESSERACT
# ============================================================================
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ============================================================================
# DETECCION DE COLOR ROJO (HSV)
# ============================================================================
# Muy Restrictivo: [150, 150] - Solo rojos muy intensos
# Restrictivo: [120, 120] - Rojos intensos
# Medio: [80, 80] - Balance
# Permisivo: [50, 50] - Mayoria de rojos
# Muy Permisivo: [20, 20] - Casi cualquier rojizo

RED_S_MIN = 150  # Saturacion minima (0-255)
RED_V_MIN = 150  # Valor/Brillo minimo (0-255)

RED_LOWER_1 = [0, RED_S_MIN, RED_V_MIN]
RED_UPPER_1 = [10, 255, 255]
RED_LOWER_2 = [170, RED_S_MIN, RED_V_MIN]
RED_UPPER_2 = [180, 255, 255]

# ============================================================================
# FILTROS GEOMETRICOS
# ============================================================================
MIN_CONTOUR_AREA = 180      # Area minima del contorno
MIN_CONTOUR_WIDTH = 18      # Ancho minimo
MIN_CONTOUR_HEIGHT = 12     # Alto minimo
MIN_ASPECT_RATIO = 0.6      # Ratio minimo w/h
MAX_ASPECT_RATIO = 6.5      # Ratio maximo w/h

# Padding para extraccion de ROI
PADDING_HORIZONTAL = 19
PADDING_VERTICAL = 12

# ============================================================================
# CONFIGURACION OCR
# ============================================================================
OCR_CONFIG_NUMBERS = "--psm 7 -c tessedit_char_whitelist=0123456789"
OCR_CONFIG_MOTOR = "--psm 6"
MIN_DIGITS = 3              # Minimo de digitos para numero valido
MAX_DIGITS = 5              # Maximo de digitos

# ============================================================================
# DETECCION DE MOTORES
# ============================================================================
MOTOR_TOP_SECTION_PCT = 0.90  # Porcentaje superior de imagen para buscar motores
MOTOR_MIN_WIDTH = 50
MOTOR_MIN_HEIGHT = 10
MOTOR_MAX_HEIGHT = 100
MOTOR_MIN_LENGTH = 8          # Longitud minima del codigo de motor

# Patrones regex para motores (en orden de prioridad)
MOTOR_PATTERNS = [
    r'\d+\.\d+/[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+',  # 1.6/EP6FADTXHPD-5GQ-5G06
    r'\d+\.\d+/[A-Z0-9]+-[A-Z0-9]+',            # 1.6/EP6FADTXHPD-5GQ
    r'\d+\.\d+/[A-Z][0-9]+[A-Z]+[0-9]*[A-Z]?',  # 1.5/B38A15P
    r'\d+\.\d+/[A-Z0-9]+',                       # Patron simple
]

# ============================================================================
# PROCESAMIENTO PARALELO
# ============================================================================
MAX_WORKERS = None  # None = usar todos los CPUs, o especificar numero (ej: 4)
PROGRESS_UPDATE_INTERVAL = 2  # Mostrar progreso cada N imagenes

# ============================================================================
# EXTENSIONES DE IMAGEN SOPORTADAS
# ============================================================================
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

# ============================================================================
# CONFIGURACION DE DEBUG
# ============================================================================
DEBUG_MODE = False  # Activar para guardar imagenes de debug

# ============================================================================
# CONFIGURACION DE UI
# ============================================================================
UI_WINDOW_TITLE = "Detector de Numeros Rojos"
UI_WINDOW_SIZE = "900x700"
UI_THEME = "clam"  # Tema de ttk: 'clam', 'alt', 'default', 'classic'

# Colores
UI_COLOR_PRIMARY = "#1976D2"
UI_COLOR_SUCCESS = "#4CAF50"
UI_COLOR_WARNING = "#FF9800"
UI_COLOR_ERROR = "#F44336"
UI_COLOR_BG = "#F5F5F5"