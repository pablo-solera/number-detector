import re
from pathlib import Path

import cv2
import numpy as np
import pytesseract

from number_detector.application.settings import DetectionSettings
from number_detector.infrastructure.imaging import OpenCVRedDetector
from number_detector.infrastructure.ocr import TesseractService
from number_detector.infrastructure.runtime import TESSERACT_CMD, check_tesseract_installed

#detector = OpenCVRedDetector(settings=DetectionSettings())
ocr = TesseractService(tesseract_cmd=TESSERACT_CMD)

img = cv2.imread('input/TEST_4.jpg')

# 1) HSV
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 2) Máscara del azul
lower_blue = np.array([112, 167, 48])
upper_blue = np.array([132, 255, 255])

mask = cv2.inRange(hsv, lower_blue, upper_blue)

# 3) Morfología: limpiar ruido y unir dígitos
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=0)   # quita puntos
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)  # une segmentos

# Unir letras/palabras en horizontal
kernel_line = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
mask = cv2.dilate(mask, kernel_line, iterations=1)

cv2.imshow('mask', mask)

# 4) Contornos (posibles "bloques" de números)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

results = []

# Config Tesseract: tratar como una sola línea o palabra (clave para enteros)
tess_config = r"--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:/.-+()"

for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)

    # Filtra contornos demasiado pequeños (ruido)
    if w < 20 or h < 10:
        continue

    # Un poco de margen alrededor
    pad = 5
    x0 = max(x - pad, 0)
    y0 = max(y - pad, 0)
    x1 = min(x + w + pad, img.shape[1])
    y1 = min(y + h + pad, img.shape[0])

    roi = img[y0:y1, x0:x1]

    # Preproceso ROI: gris + agrandar + binarizar
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # OCR
    text = pytesseract.image_to_string(thr, config=tess_config)

    if text:
        results.append({
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "texto": text
        })




# Ordenar por posición (por ejemplo de izquierda a derecha)
# ordenar de arriba a abajo y de izquierda a derecha
results.sort(key=lambda r: (r["y"], r["x"]))

for i, r in enumerate(results, start=1):
    print(f"{i}. [{r['x']},{r['y']},{r['w']},{r['h']}]")
    print(r["texto"])
    print("-" * 40)

cv2.imshow('gray', hsv)

cv2.waitKey(0)
# TODO: show results as json
