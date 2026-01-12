"""
Script de diagnóstico para visualizar la detección de números rojos
Guarda en: red-number-detector/diagnostic.py
"""

import cv2
import numpy as np
import pytesseract
from pathlib import Path
import config

if config.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


def visualize_red_detection(image_path, output_folder='output/diagnostic'):
    """
    Visualiza paso a paso la detección de números rojos
    """
    # Crear carpeta de salida
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Leer imagen
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Error al leer la imagen: {image_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"📸 Procesando: {Path(image_path).name}")
    print(f"{'='*60}")
    
    # 1. Mostrar imagen original
    original_copy = image.copy()
    
    # 2. Convertir a HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 3. Crear máscaras de rojo con DIFERENTES rangos para probar
    print("\n🔍 Probando diferentes rangos de detección de rojo:")
    
    # Rango 1: Muy permisivo (detecta más rojos)
    lower_red1_loose = np.array([0, 30, 30])
    upper_red1_loose = np.array([10, 255, 255])
    lower_red2_loose = np.array([170, 30, 30])
    upper_red2_loose = np.array([180, 255, 255])
    
    mask1_loose = cv2.inRange(hsv, lower_red1_loose, upper_red1_loose)
    mask2_loose = cv2.inRange(hsv, lower_red2_loose, upper_red2_loose)
    red_mask_loose = cv2.bitwise_or(mask1_loose, mask2_loose)
    
    # Rango 2: Configuración actual
    lower_red1 = np.array(config.RED_LOWER_1)
    upper_red1 = np.array(config.RED_UPPER_1)
    lower_red2 = np.array(config.RED_LOWER_2)
    upper_red2 = np.array(config.RED_UPPER_2)
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask_current = cv2.bitwise_or(mask1, mask2)
    
    # Rango 3: Más restrictivo
    lower_red1_strict = np.array([0, 120, 120])
    upper_red1_strict = np.array([10, 255, 255])
    lower_red2_strict = np.array([170, 120, 120])
    upper_red2_strict = np.array([180, 255, 255])
    
    mask1_strict = cv2.inRange(hsv, lower_red1_strict, upper_red1_strict)
    mask2_strict = cv2.inRange(hsv, lower_red2_strict, upper_red2_strict)
    red_mask_strict = cv2.bitwise_or(mask1_strict, mask2_strict)
    
    # Aplicar operaciones morfológicas
    kernel = np.ones((3, 3), np.uint8)
    
    red_mask_loose = cv2.morphologyEx(red_mask_loose, cv2.MORPH_CLOSE, kernel)
    red_mask_loose = cv2.morphologyEx(red_mask_loose, cv2.MORPH_OPEN, kernel)
    
    red_mask_current = cv2.morphologyEx(red_mask_current, cv2.MORPH_CLOSE, kernel)
    red_mask_current = cv2.morphologyEx(red_mask_current, cv2.MORPH_OPEN, kernel)
    
    red_mask_strict = cv2.morphologyEx(red_mask_strict, cv2.MORPH_CLOSE, kernel)
    red_mask_strict = cv2.morphologyEx(red_mask_strict, cv2.MORPH_OPEN, kernel)
    
    # Guardar máscaras
    base_name = Path(image_path).stem
    cv2.imwrite(str(output_path / f"{base_name}_1_mask_loose.jpg"), red_mask_loose)
    cv2.imwrite(str(output_path / f"{base_name}_2_mask_current.jpg"), red_mask_current)
    cv2.imwrite(str(output_path / f"{base_name}_3_mask_strict.jpg"), red_mask_strict)
    
    print(f"   ✅ Máscaras guardadas en: {output_path}")
    
    # 4. Detectar y procesar contornos para cada máscara
    masks_info = [
        ("Permisivo [30-255]", red_mask_loose, (0, 255, 0)),
        ("Actual [50-255]", red_mask_current, (255, 165, 0)),
        ("Restrictivo [120-255]", red_mask_strict, (0, 0, 255))
    ]
    
    for mask_name, mask, color in masks_info:
        print(f"\n📊 Rango {mask_name}:")
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"   Contornos encontrados: {len(contours)}")
        
        image_with_boxes = image.copy()
        numbers_found = []
        
        for idx, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Mostrar TODOS los contornos encontrados
            cv2.rectangle(image_with_boxes, (x, y), (x+w, y+h), color, 2)
            cv2.putText(image_with_boxes, f"{idx}", (x, y-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Filtrar por tamaño mínimo
            if w < config.MIN_CONTOUR_WIDTH or h < config.MIN_CONTOUR_HEIGHT:
                print(f"   [{idx}] Descartado por tamaño: {w}x{h} (área: {area:.0f})")
                continue
            
            print(f"   [{idx}] Contorno válido: {w}x{h} (área: {area:.0f})")
            
            # Expandir área
            padding = config.CONTOUR_PADDING
            x_pad = max(0, x - padding)
            y_pad = max(0, y - padding)
            w_pad = min(image.shape[1] - x_pad, w + 2 * padding)
            h_pad = min(image.shape[0] - y_pad, h + 2 * padding)
            
            # Extraer ROI
            roi = image[y_pad:y_pad+h_pad, x_pad:x_pad+w_pad]
            
            # Guardar ROI
            roi_path = output_path / f"{base_name}_{mask_name.split()[0]}_roi_{idx}.jpg"
            cv2.imwrite(str(roi_path), roi)
            
            # OCR
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, thresh_roi = cv2.threshold(gray_roi, 0, 255, 
                                         cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Probar diferentes configuraciones de Tesseract
            configs = [
                ('PSM 6', r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'),
                ('PSM 7', r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'),
                ('PSM 8', r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'),
            ]
            
            for config_name, tesseract_config in configs:
                text = pytesseract.image_to_string(thresh_roi, config=tesseract_config)
                text = ''.join(filter(str.isdigit, text))
                
                if text and len(text) >= config.MIN_DIGITS:
                    print(f"       OCR {config_name}: '{text}' ✓")
                    numbers_found.append(text)
                    break
            else:
                print(f"       OCR: No se detectó número válido")
        
        # Guardar imagen con cajas
        output_file = output_path / f"{base_name}_4_{mask_name.split()[0]}_boxes.jpg"
        cv2.imwrite(str(output_file), image_with_boxes)
        
        if numbers_found:
            print(f"   ✅ Números detectados: {numbers_found}")
        else:
            print(f"   ⚠️  No se detectaron números válidos")
    
    print(f"\n{'='*60}")
    print(f"✅ Diagnóstico completado")
    print(f"📁 Archivos guardados en: {output_path}/")
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
    images = []
    for ext in config.IMAGE_EXTENSIONS:
        images.extend(folder.glob(f"*{ext}"))
    
    if not images:
        print(f"⚠️  No se encontraron imágenes en {folder_path}")
        return
    
    print(f"\n🔬 DIAGNÓSTICO DE DETECCIÓN DE NÚMEROS ROJOS")
    print(f"📁 Carpeta: {folder_path}")
    print(f"🖼️  Imágenes encontradas: {len(images)}\n")
    
    for image_path in sorted(images):
        visualize_red_detection(image_path, output_folder)
    
    print(f"\n{'='*70}")
    print(f"🎯 INSTRUCCIONES:")
    print(f"{'='*70}")
    print(f"1. Revisa las imágenes en: {output_folder}/")
    print(f"2. Busca el archivo *_mask_*.jpg que mejor detecte los números rojos")
    print(f"3. Busca el archivo *_boxes.jpg para ver las cajas detectadas")
    print(f"4. Si 'Permisivo' detecta los números, actualiza config.py con:")
    print(f"   RED_LOWER_1 = [0, 30, 30]")
    print(f"   RED_LOWER_2 = [170, 30, 30]")
    print(f"5. Si 'Restrictivo' funciona mejor, usa:")
    print(f"   RED_LOWER_1 = [0, 120, 120]")
    print(f"   RED_LOWER_2 = [170, 120, 120]")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # Analizar todas las imágenes
    analyze_folder('input', 'output/diagnostic')
    
    # O analizar una imagen específica:
    # visualize_red_detection('input/16_26_1.jpg', 'output/diagnostic')
