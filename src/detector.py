import cv2
import pytesseract
import re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import config
from numpy import array

pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


class RedNumberDetector:

    def __init__(self, debug=False, debug_dir=None):
        self.debug = debug
        self.debug_dir = Path(debug_dir) if debug_dir else None

        if self.debug and self.debug_dir:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

        # OCR SOLO NUMEROS
        self.OCR_CONFIG = config.OCR_CONFIG_NUMBERS
        self.OCR_CONFIG_MOTOR = config.OCR_CONFIG_MOTOR

    def process(self, image_path: Path):
        """Procesa una sola imagen"""
        image = cv2.imread(str(image_path))
        if image is None:
            return [], []

        numbers = self._detect_red_numbers(image, image_path.stem)
        motors = self._detect_motor(image, image_path.stem)

        return numbers, motors

    def process_batch(self, image_paths, max_workers=None, progress_callback=None):
        """
        Procesa multiples imagenes en paralelo

        Args:
            image_paths: Lista de Path de imagenes
            max_workers: Numero de procesos paralelos (None = usar todos los CPUs)
            progress_callback: Funcion callback(current, total, image_name) para reportar progreso

        Returns:
            dict: {image_path: (numbers, motors)}
        """
        if max_workers is None:
            max_workers = cpu_count()

        results = {}
        total = len(image_paths)

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

                    # Llamar callback de progreso si existe
                    if progress_callback:
                        progress_callback(completed, total, image_path.name)

                except Exception as e:
                    print(f"Error procesando {image_path.name}: {e}")
                    results[image_path] = ([], [])
                    completed += 1

                    if progress_callback:
                        progress_callback(completed, total, image_path.name)

        return results

    @staticmethod
    def _process_single(image_path):
        """
        Funcion estatica para procesamiento paralelo
        """
        detector = RedNumberDetector(debug=False, debug_dir=None)
        return detector.process(image_path)

    def _detect_motor(self, image, name):
        """Detecta TODOS los codigos de motor"""
        height, width = image.shape[:2]

        top_section = image[0:int(height * config.MOTOR_TOP_SECTION_PCT), :]

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_region.png"), top_section)

        gray = cv2.cvtColor(top_section, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_thresh.png"), thresh)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 3))
        dilated = cv2.dilate(thresh, kernel, iterations=1)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_motor_dilated.png"), dilated)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motor_candidates = []
        debug_img = top_section.copy()

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            if w < config.MOTOR_MIN_WIDTH or h < config.MOTOR_MIN_HEIGHT or \
                    w > width * 0.6 or h > config.MOTOR_MAX_HEIGHT:
                continue

            pad = 5
            x1 = max(x - pad, 0)
            y1 = max(y - pad, 0)
            x2 = min(x + w + pad, top_section.shape[1])
            y2 = min(y + h + pad, top_section.shape[0])

            roi = top_section[y1:y2, x1:x2]
            roi_scaled = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            text = pytesseract.image_to_string(roi_scaled, config=self.OCR_CONFIG_MOTOR)
            text = text.strip()

            if self.debug:
                print(f"   ROI text RAW:\n{text}\n")

            lines = text.split('\n')
            motor_parts = []
            for line in lines:
                line = line.strip()
                if not line or 'kw:' in line.lower() or 'idveic' in line.lower() or 'cv:' in line.lower():
                    break
                motor_parts.append(line)

            motor_text = ''.join(motor_parts)

            if self.debug:
                print(f"   Motor text joined: '{motor_text}'")

            for motor_pattern in config.MOTOR_PATTERNS:
                match = re.search(motor_pattern, motor_text)

                if match:
                    motor_code = match.group()

                    if len(motor_code) >= config.MOTOR_MIN_LENGTH and motor_code not in motor_candidates:
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

        lower_red_1 = array(config.RED_LOWER_1)
        upper_red_1 = array(config.RED_UPPER_1)
        lower_red_2 = array(config.RED_LOWER_2)
        upper_red_2 = array(config.RED_UPPER_2)

        mask1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
        mask2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
        mask = cv2.bitwise_or(mask1, mask2)

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

            if area < config.MIN_CONTOUR_AREA:
                continue
            if w < config.MIN_CONTOUR_WIDTH or h < config.MIN_CONTOUR_HEIGHT:
                continue
            ratio = w / h
            if ratio < config.MIN_ASPECT_RATIO or ratio > config.MAX_ASPECT_RATIO:
                continue

            x1 = max(x - config.PADDING_HORIZONTAL, 0)
            y1 = max(y - config.PADDING_VERTICAL, 0)
            x2 = min(x + w + config.PADDING_HORIZONTAL, image.shape[1])
            y2 = min(y + h + config.PADDING_VERTICAL, image.shape[0])

            roi = image[y1:y2, x1:x2]

            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            text = pytesseract.image_to_string(gray, config=self.OCR_CONFIG)
            text = text.strip()

            if not re.fullmatch(rf"\d{{{config.MIN_DIGITS},{config.MAX_DIGITS}}}", text):
                inverted = cv2.bitwise_not(gray)
                text = pytesseract.image_to_string(inverted, config=self.OCR_CONFIG)
                text = text.strip()

            if re.fullmatch(rf"\d{{{config.MIN_DIGITS},{config.MAX_DIGITS}}}", text):
                detected.add(text)

                if self.debug:
                    cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(debug_img, text, (x1, y1 - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if self.debug:
            cv2.imwrite(str(self.debug_dir / f"{name}_debug.png"), debug_img)

        return sorted(detected, key=int)