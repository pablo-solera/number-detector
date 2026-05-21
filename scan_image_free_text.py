import json

import cv2
import numpy as np
import pytesseract
import re

from number_detector.infrastructure.ocr import TesseractService
from number_detector.infrastructure.runtime import TESSERACT_CMD

# =========================
# CONFIG
# =========================
IMAGE_PATH = "input/TEST_4.jpg"

# PON AQUÍ tus valores ya ajustados
lower_blue = np.array([51, 35, 74], dtype=np.uint8)
upper_blue = np.array([71, 255, 255], dtype=np.uint8)

# Si Tesseract no está en PATH, descomenta y ajusta:
#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
ocr = TesseractService(tesseract_cmd=TESSERACT_CMD)

# =========================
# FUNCIONES
# =========================
def limpiar_texto(texto):
    texto = texto.strip()
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n", texto)
    return texto

def preparar_roi_para_ocr(roi_bgr):
    gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thr

# =========================
# CARGA IMAGEN
# =========================
img = cv2.imread(IMAGE_PATH)
if img is None:
    raise FileNotFoundError(f"No se pudo leer la imagen: {IMAGE_PATH}")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# =========================
# MÁSCARA AZUL
# =========================
mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Limpieza
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=0)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

# Unir letras/palabras en horizontal
kernel_line = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
mask = cv2.dilate(mask, kernel_line, iterations=1)

# =========================
# BUSCAR BLOQUES AZULES
# =========================
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# OCR pensado para texto azul tipo motor
config_tesseract = (
    r'--oem 3 --psm 6 '
    r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    r'0123456789:/.-+()'
)

resultados = []
img_boxes = img.copy()

for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)

    # filtrar ruido
    if w < 20 or h < 10:
        continue

    # margen
    pad = 5
    x0 = max(x - pad, 0)
    y0 = max(y - pad, 0)
    x1 = min(x + w + pad, img.shape[1])
    y1 = min(y + h + pad, img.shape[0])

    roi = img[y0:y1, x0:x1]
    roi_ocr = preparar_roi_para_ocr(roi)

    texto = pytesseract.image_to_string(roi_ocr, config=config_tesseract)
    texto = limpiar_texto(texto)

    if texto:


        print(texto)



        # dibujar caja
        cv2.rectangle(img_boxes, (x0, y0), (x1, y1), (0, 255, 0), 2)

# ordenar por potencia
resultados.sort(key=lambda x: x["kw"] if x["kw"] else 0)

# =========================
# JSON FINAL
# =========================

json_resultado = json.dumps(resultados, indent=4)

print("\n=== FREE TEXT DETECTADOS ===\n")
print(json_resultado)
# Ventanas para revisar visualmente
cv2.imshow("Mascara azul", mask)
cv2.imshow("Bloques detectados", img_boxes)

cv2.waitKey(0)
cv2.destroyAllWindows()
