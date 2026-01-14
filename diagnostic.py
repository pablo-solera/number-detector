"""
Script de diagnóstico para visualizar la detección de números rojos y motores
Guarda en: red-number-detector/diagnostic.py
"""

import cv2
import numpy as np
import pytesseract
from pathlib import Path
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def visualize_red_detection(image_path, output_folder='output/diagnostic'):
    """
    Visualiza paso a paso la detección de números rojos
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Error al leer la imagen: {image_path}")
        return

    print(f"\n{'='*60}")
    print(f"📸 Procesando: {Path(image_path).name}")
    print(f"{'='*60}")

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Definir 5 rangos diferentes para probar
    ranges = [
        ("Muy Permisivo [20-255]", [0, 20, 20], [10, 255, 255], [170, 20, 20], [180, 255, 255], (0, 255, 0)),
        ("Permisivo [50-255]", [0, 50, 50], [10, 255, 255], [170, 50, 50], [180, 255, 255], (0, 200, 200)),
        ("Medio [80-255]", [0, 80, 80], [10, 255, 255], [170, 80, 80], [180, 255, 255], (255, 165, 0)),
        ("Restrictivo [120-255]", [0, 120, 120], [10, 255, 255], [170, 120, 120], [180, 255, 255], (255, 0, 0)),
        ("Muy Restrictivo [150-255]", [0, 150, 150], [10, 255, 255], [170, 150, 150], [180, 255, 255], (0, 0, 255))
    ]

    print("\n🔍 Probando diferentes rangos de detección de rojo:\n")

    base_name = Path(image_path).stem
    all_results = []

    for idx, (name, lower1, upper1, lower2, upper2, color) in enumerate(ranges):
        print(f"📊 Rango {idx+1}: {name}")

        # Crear máscaras
        mask1 = cv2.inRange(hsv, np.array(lower1), np.array(upper1))
        mask2 = cv2.inRange(hsv, np.array(lower2), np.array(upper2))
        mask = cv2.bitwise_or(mask1, mask2)

        # Operaciones morfológicas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.dilate(mask, kernel, iterations=1)

        # Guardar máscara
        cv2.imwrite(str(output_path / f"{base_name}_{idx+1}_mask_{name.split()[0]}.jpg"), mask)

        # Detectar contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"   Contornos encontrados: {len(contours)}")

        image_with_boxes = image.copy()
        numbers_found = []

        for cnt_idx, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            # Filtros geométricos
            if area < 180 or w < 18 or h < 12:
                continue

            ratio = w / h
            if ratio < 0.6 or ratio > 6.5:
                continue

            # Padding
            pad_h, pad_v = 19, 12
            x1 = max(x - pad_h, 0)
            y1 = max(y - pad_v, 0)
            x2 = min(x + w + pad_h, image.shape[1])
            y2 = min(y + h + pad_v, image.shape[0])

            roi = image[y1:y2, x1:x2]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            # OCR
            text = pytesseract.image_to_string(thresh, config="--psm 7 -c tessedit_char_whitelist=0123456789")
            text = text.strip()

            if re.fullmatch(r"\d{3,5}", text):
                numbers_found.append(text)
                cv2.rectangle(image_with_boxes, (x1, y1), (x2, y2), color, 2)
                cv2.putText(image_with_boxes, text, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Guardar imagen con cajas
        cv2.imwrite(str(output_path / f"{base_name}_{idx+1}_boxes_{name.split()[0]}.jpg"), image_with_boxes)

        numbers_sorted = sorted(set(numbers_found), key=int) if numbers_found else []
        print(f"   ✅ Números detectados: {numbers_sorted}\n")

        all_results.append({
            'name': name,
            'numbers': numbers_sorted,
            'count': len(numbers_sorted)
        })

    # Resumen
    print(f"{'='*60}")
    print("📈 RESUMEN DE RESULTADOS:")
    print(f"{'='*60}")
    for idx, result in enumerate(all_results):
        print(f"{idx+1}. {result['name']}: {result['count']} números → {result['numbers']}")
    print(f"{'='*60}\n")


def visualize_motor_detection(image_path, output_folder='output/diagnostic'):
    """
    Visualiza la detección de motores en la imagen
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Error al leer la imagen: {image_path}")
        return

    print(f"\n{'='*60}")
    print(f"🚗 DETECCIÓN DE MOTORES: {Path(image_path).name}")
    print(f"{'='*60}\n")

    height, width = image.shape[:2]
    base_name = Path(image_path).stem

    # Probar diferentes porcentajes de la imagen
    percentages = [0.9]

    for pct in percentages:
        print(f"📊 Analizando {int(pct*100)}% superior de la imagen:")

        top_section = image[0:int(height * pct), :]

        # Guardar región
        cv2.imwrite(str(output_path / f"{base_name}_motor_region_{int(pct*100)}pct.jpg"), top_section)

        # Convertir a gris y umbralizar
        gray = cv2.cvtColor(top_section, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Guardar umbralización
        cv2.imwrite(str(output_path / f"{base_name}_motor_thresh_{int(pct*100)}pct.jpg"), thresh)

        # Dilatar
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 3))
        dilated = cv2.dilate(thresh, kernel, iterations=1)

        # Guardar dilatado
        cv2.imwrite(str(output_path / f"{base_name}_motor_dilated_{int(pct*100)}pct.jpg"), dilated)

        # Detectar contornos
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"   Contornos encontrados: {len(contours)}")

        debug_img = top_section.copy()
        motors_found = []

        for cnt_idx, cnt in enumerate(contours):
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
            text = pytesseract.image_to_string(roi_scaled, config="--psm 6")
            text = text.strip()

            print(f"   [{cnt_idx}] ROI text: {repr(text[:100])}")

            # Separar por líneas y construir motor
            lines = text.split('\n')
            motor_parts = []
            for line in lines:
                line = line.strip()
                if not line or 'kw:' in line.lower() or 'idveic' in line.lower() or 'cv:' in line.lower():
                    break
                motor_parts.append(line)

            motor_text = ''.join(motor_parts)

            # Patrones de motor
            motor_patterns = [
                r'\d+\.\d+/[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+',
                r'\d+\.\d+/[A-Z0-9]+-[A-Z0-9]+',
                r'\d+\.\d+/[A-Z][0-9]+[A-Z]+[0-9]*[A-Z]?',
                r'\d+\.\d+/[A-Z0-9]+',
            ]

            for pattern in motor_patterns:
                match = re.search(pattern, motor_text)
                if match:
                    motor_code = match.group()
                    if len(motor_code) >= 8 and motor_code not in motors_found:
                        motors_found.append(motor_code)
                        print(f"       ✓ Motor detectado: {motor_code}")

                        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (255, 0, 0), 2)
                        cv2.putText(debug_img, motor_code[:20], (x, y-5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                    break

        # Guardar debug
        cv2.imwrite(str(output_path / f"{base_name}_motor_boxes_{int(pct*100)}pct.jpg"), debug_img)

        print(f"   ✅ Motores encontrados: {motors_found}\n")

    print(f"{'='*60}\n")


def analyze_folder(folder_path='input', output_folder='output/diagnostic'):
    """
    Analiza todas las imágenes de una carpeta
    """
    folder = Path(folder_path)

    if not folder.exists():
        print(f"❌ La carpeta {folder_path} no existe")
        return

    # Obtener todas las imágenes
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    images = []
    for ext in image_extensions:
        images.extend(folder.glob(f"*{ext}"))

    if not images:
        print(f"⚠️ No se encontraron imágenes en {folder_path}")
        return

    print(f"\n🔬 DIAGNÓSTICO COMPLETO")
    print(f"📁 Carpeta: {folder_path}")
    print(f"🖼️ Imágenes encontradas: {len(images)}\n")

    for image_path in sorted(images):
        # Analizar números rojos
        visualize_red_detection(image_path, output_folder)

        # Analizar motores
        visualize_motor_detection(image_path, output_folder)

    print(f"\n{'='*70}")
    print(f"🎯 INSTRUCCIONES:")
    print(f"{'='*70}")
    print(f"1. Revisa las imágenes en: {output_folder}/")
    print(f"2. Para NÚMEROS ROJOS:")
    print(f"   - Busca *_mask_*.jpg para ver qué rango detecta mejor")
    print(f"   - Busca *_boxes_*.jpg para ver las cajas sobre los números")
    print(f"3. Para MOTORES:")
    print(f"   - Busca *_motor_region_*.jpg para ver la zona analizada")
    print(f"   - Busca *_motor_boxes_*.jpg para ver los motores detectados")
    print(f"   - Prueba diferentes porcentajes (15%, 20%, 25%, etc.)")
    print(f"4. Ajusta config.py o detector.py según los mejores resultados")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # Analizar todas las imágenes
    analyze_folder('input', 'output/diagnostic')

    # O analizar una imagen específica:
    # visualize_red_detection('input/508.jpg', 'output/diagnostic')
    # visualize_motor_detection('input/508.jpg', 'output/diagnostic')