import cv2
import pytesseract
import numpy as np
import re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


class RedNumberDetector:

    def __init__(self, debug=False, debug_dir=None):
        self.debug = debug
        self.debug_dir = Path(debug_dir) if debug_dir else None

        if self.debug and self.debug_dir:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

        # OCR SOLO NUMEROS
        self.OCR_CONFIG = "--psm 7 -c tessedit_char_whitelist=0123456789"

        # OCR para texto del motor
        self.OCR_CONFIG_MOTOR = "--psm 6"

    def process(self, image_path: Path):
        """Procesa una sola imagen"""
        image = cv2.imread(str(image_path))
        if image is None:
            return [], []

        numbers = self._detect_red_numbers(image, image_path.stem)
        motors = self._detect_motor(image, image_path.stem)

        print(f"\n[{image_path.name}] Numeros: {len(numbers)} | Motores: {len(motors)}")

        return numbers, motors

    def process_batch(self, image_paths, max_workers=None):
        """
        Procesa multiples imagenes en paralelo

        Args:
            image_paths: Lista de Path de imagenes
            max_workers: Numero de procesos paralelos (None = usar todos los CPUs)

        Returns:
            dict: {image_path: (numbers, motors)}
        """
        if max_workers is None:
            max_workers = cpu_count()

        print(f"\n{'=' * 70}")
        print(f"PROCESAMIENTO EN PARALELO")
        print(f"{'=' * 70}")
        print(f"Imagenes a procesar: {len(image_paths)}")
        print(f"Procesos paralelos: {max_workers}")
        print(f"{'=' * 70}\n")

        results = {}

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            future_to_path = {
                executor.submit(self._process_single, path): path
                for path in image_paths
            }

            # Procesar resultados a medida que se completan
            completed = 0
            for future in as_completed(future_to_path):
                image_path = future_to_path[future]
                try:
                    numbers, motors = future.result()
                    results[image_path] = (numbers, motors)
                    completed += 1

                    # Mostrar progreso
                    if completed % 10 == 0 or completed == len(image_paths):
                        progress = (completed / len(image_paths)) * 100
                        print(f"Progreso: {completed}/{len(image_paths)} ({progress:.1f}%)")

                except Exception as e:
                    print(f"Error procesando {image_path.name}: {e}")
                    results[image_path] = ([], [])

        print(f"\n{'=' * 70}")
        print(f"PROCESAMIENTO COMPLETADO")
        print(f"Imagenes procesadas exitosamente: {len(results)}")
        print(f"{'=' * 70}\n")

        return results

    @staticmethod
    def _process_single(image_path):
        """
        Funcion estatica para procesamiento paralelo
        (necesaria para que ProcessPoolExecutor funcione)
        """
        detector = RedNumberDetector(debug=False, debug_dir=None)
        return detector.process(image_path)

    def _detect_motor(self, image, name):
        """
        Detecta TODOS los codigos de motor en la parte superior de la imagen
        """
        height, width = image.shape[:2]

        # Tomar solo el 25% superior de la imagen
        top_section = image[0:int(height * 0.90), :]

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_region.png"), top_section)

        # Convertir a escala de grises
        gray = cv2.cvtColor(top_section, cv2.COLOR_BGR2GRAY)

        # Umbralizacion
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_thresh.png"), thresh)

        # Buscar regiones con texto
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 3))
        dilated = cv2.dilate(thresh, kernel, iterations=1)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_dilated.png"), dilated)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motor_candidates = []
        debug_img = top_section.copy()

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            # Filtros
            if w < 50 or h < 10 or w > width * 0.6 or h > 100:
                continue

            # ROI con padding
            pad = 5
            x1 = max(x - pad, 0)
            y1 = max(y - pad, 0)
            x2 = min(x + w + pad, top_section.shape[1])
            y2 = min(y + h + pad, top_section.shape[0])

            roi = top_section[y1:y2, x1:x2]

            # Escalar para mejor OCR
            roi_scaled = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            # OCR
            text = pytesseract.image_to_string(roi_scaled, config=self.OCR_CONFIG_MOTOR)
            text = text.strip()

            if self.debug:
                print(f"   ROI text RAW:\n{text}\n")

            # Separar por lineas
            lines = text.split('\n')

            # Construir el codigo del motor
            motor_parts = []
            for line in lines:
                line = line.strip()
                if not line or 'kw:' in line.lower() or 'idveic' in line.lower() or 'cv:' in line.lower():
                    break
                motor_parts.append(line)

            motor_text = ''.join(motor_parts)

            if self.debug:
                print(f"   Motor text joined: '{motor_text}'")

            # Patrones de motor
            motor_patterns = [
                r'\d+\.\d+/[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+',
                r'\d+\.\d+/[A-Z0-9]+-[A-Z0-9]+',
                r'\d+\.\d+/[A-Z][0-9]+[A-Z]+[0-9]*[A-Z]?',
                r'\d+\.\d+/[A-Z0-9]+',
            ]

            for motor_pattern in motor_patterns:
                match = re.search(motor_pattern, motor_text)

                if match:
                    motor_code = match.group()

                    if len(motor_code) >= 8 and motor_code not in motor_candidates:
                        motor_candidates.append(motor_code)

                        if self.debug:
                            cv2.rectangle(debug_img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                            cv2.putText(debug_img, motor_code[:20], (x, y - 5),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

                    break

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_debug.png"), debug_img)
            print(f"   Motor candidates: {motor_candidates}")

        return motor_candidates if motor_candidates else []

    def _detect_red_numbers(self, image, name):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # VALORES MUY RESTRICTIVOS (solo rojos muy intensos)
        lower_red_1 = np.array([0, 150, 150])
        upper_red_1 = np.array([10, 255, 255])

        lower_red_2 = np.array([170, 150, 150])
        upper_red_2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
        mask2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
        mask = cv2.bitwise_or(mask1, mask2)

        # Limpieza morfologica
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

            # Filtros geometricos
            if area < 180:
                continue
            if w < 18 or h < 12:
                continue
            ratio = w / h
            if ratio < 0.6 or ratio > 6.5:
                continue

            # Padding asimetrico
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

            if not re.fullmatch(r"\d{3,5}", text):
                inverted = cv2.bitwise_not(gray)
                text = pytesseract.image_to_string(inverted, config=self.OCR_CONFIG)
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