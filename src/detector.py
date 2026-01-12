import cv2
import pytesseract
import numpy as np
import re
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

class RedNumberDetector:

    def __init__(self, debug=False, debug_dir=None):
        self.debug = debug
        self.debug_dir = Path(debug_dir) if debug_dir else None

        if self.debug and self.debug_dir:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

        # OCR SOLO NÚMEROS
        self.OCR_CONFIG = "--psm 7 -c tessedit_char_whitelist=0123456789"

    def process(self, image_path: Path):
        image = cv2.imread(str(image_path))
        if image is None:
            return [], None

        numbers = self._detect_red_numbers(image, image_path.stem)

        print(f"\nIMAGEN: {image_path.name}")
        print(f"NÚMEROS DETECTADOS: {numbers}")

        # Motor lo dejamos vacío por ahora (lo haremos después bien)
        return numbers, None

    def _detect_red_numbers(self, image, name):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Rojo tiene dos rangos en HSV
        lower_red_1 = np.array([0, 120, 120])
        upper_red_1 = np.array([10, 255, 255])

        lower_red_2 = np.array([170, 120, 120])
        upper_red_2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
        mask2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
        mask = cv2.bitwise_or(mask1, mask2)

        # Limpieza morfológica (CLAVE)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.dilate(mask, kernel, iterations=1)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_mask.png"), mask)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected = set()
        debug_img = image.copy()

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h

            # Filtros geométricos afinados para TU imagen
            if area < 180:
                continue
            if w < 18 or h < 12:
                continue
            ratio = w / h
            if ratio < 0.6 or ratio > 6.5:
                continue

            # Padding GRANDE para no cortar dígitos
            pad = 12
            x1 = max(x - pad, 0)
            y1 = max(y - pad, 0)
            x2 = min(x + w + pad, image.shape[1])
            y2 = min(y + h + pad, image.shape[0])

            roi = image[y1:y2, x1:x2]

            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255,
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            text = pytesseract.image_to_string(gray, config=self.OCR_CONFIG)
            text = text.strip()

            if re.fullmatch(r"\d{3,5}", text):
                detected.add(text)

                if self.debug:
                    cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(debug_img, text, (x1, y1 - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_debug.png"), debug_img)

        return sorted(detected, key=int)
