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

        # OCR para texto del motor (números, letras, /, :)
        self.OCR_CONFIG_MOTOR = "--psm 6"

    def process(self, image_path: Path):
        image = cv2.imread(str(image_path))
        if image is None:
            return [], None

        numbers = self._detect_red_numbers(image, image_path.stem)
        motor = self._detect_motor(image, image_path.stem)

        print(f"\nIMAGEN: {image_path.name}")
        print(f"NÚMEROS DETECTADOS: {numbers}")
        print(f"MOTOR DETECTADO: {motor}")

        return numbers, motor

    def _detect_motor(self, image, name):
        """
        Detecta el código del motor en la parte superior de la imagen
        Busca patrones como: 1.5/B38A15P
        """
        height, width = image.shape[:2]

        # Tomar solo el 20% superior de la imagen (donde está el motor)
        top_section = image[0:int(height * 0.40), :]

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_region.png"), top_section)

        # Convertir a escala de grises
        gray = cv2.cvtColor(top_section, cv2.COLOR_BGR2GRAY)

        # Umbralización para texto oscuro sobre fondo claro
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_thresh.png"), thresh)

        # Buscar regiones con texto (rectángulos con texto potencial)
        # Primero, dilatar para conectar letras cercanas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 3))
        dilated = cv2.dilate(thresh, kernel, iterations=1)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_dilated.png"), dilated)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motor_candidates = []
        debug_img = top_section.copy()

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            # Filtrar regiones muy pequeñas o muy grandes
            if w < 50 or h < 10 or w > width * 0.5 or h > 50:
                continue

            # Extraer ROI
            roi = top_section[y:y + h, x:x + w]

            # OCR en la región
            text = pytesseract.image_to_string(roi, config=self.OCR_CONFIG_MOTOR)
            text = text.strip().replace('\n', ' ').replace('  ', ' ')

            # Buscar patrón de motor: número.número/LETRAS+NÚMEROS
            # Ejemplos: 1.5/B38A15P, 2.0/B48A20A, etc.
            motor_pattern = r'\d+\.\d+/[A-Z0-9]+[A-Z]\d+[A-Z]?'
            match = re.search(motor_pattern, text)

            if match:
                motor_code = match.group()
                motor_candidates.append(motor_code)

                if self.debug:
                    cv2.rectangle(debug_img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(debug_img, motor_code, (x, y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_debug.png"), debug_img)

        # Retornar el primer candidato válido (o None si no se encontró)
        return motor_candidates[0] if motor_candidates else None

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

        # Limpieza morfológica
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

            # Filtros geométricos
            if area < 180:
                continue
            if w < 18 or h < 12:
                continue
            ratio = w / h
            if ratio < 0.6 or ratio > 6.5:
                continue

            # Padding asimétrico
            pad_horizontal = 19
            pad_vertical = 12

            x1 = max(x - pad_horizontal, 0)
            y1 = max(y - pad_vertical, 0)
            x2 = min(x + w + pad_horizontal, image.shape[1])
            y2 = min(y + h + pad_vertical, image.shape[0])

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