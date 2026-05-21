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

# 2) Máscara del rojo (dos rangos en HSV)
lower1 = np.array([0, 120, 70])
upper1 = np.array([10, 255, 255])
lower2 = np.array([170, 120, 70])
upper2 = np.array([180, 255, 255])

mask1 = cv2.inRange(hsv, lower1, upper1)
mask2 = cv2.inRange(hsv, lower2, upper2)
mask = cv2.bitwise_or(mask1, mask2)

# 3) Morfología: limpiar ruido y unir dígitos
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)   # quita puntos
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=5)  # une segmentos

cv2.imshow('mask', mask)

# 4) Contornos (posibles "bloques" de números)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

results = []

# Config Tesseract: tratar como una sola línea o palabra (clave para enteros)
tess_config = r"--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789"

for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)

    # Filtra contornos demasiado pequeños (ruido)
    if w < 20 or h < 15:
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

    # Extraer números completos (grupos), no dígitos
    nums = re.findall(r"\d+", text)

    # Normalmente habrá 0 o 1 número por ROI; si hay varios, los unes o eliges el más largo
    if nums:
        num = max(nums, key=len)  # el más largo suele ser el correcto
        results.append((x, y, num))

# Ordenar por posición (por ejemplo de izquierda a derecha)
results.sort(key=lambda t: (t[1], t[0]))
print("Números detectados:", [n for (_, _, n) in results])

cv2.imshow('gray', hsv)

cv2.waitKey(0)

