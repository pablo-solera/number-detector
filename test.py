import cv2
import numpy as np
import pytesseract
import pandas as pd
import os
from pathlib import Path
import re

# Si estás en Windows, descomenta y ajusta la ruta de Tesseract:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def detect_red_color(image):
    """
    Detecta áreas rojas en la imagen usando HSV color space
    """
    # Convertir a HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Definir rangos para el color rojo (el rojo está en dos extremos del espectro HSV)
    # Rojo bajo (0-10)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    
    # Rojo alto (170-180)
    lower_red2 = np.array([170, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    # Crear máscaras
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    
    # Combinar máscaras
    red_mask = cv2.bitwise_or(mask1, mask2)
    
    # Aplicar operaciones morfológicas para limpiar la máscara
    kernel = np.ones((3, 3), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    
    return red_mask

def extract_red_numbers(image_path):
    """
    Extrae números rojos de una imagen
    """
    # Leer imagen
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Error al leer la imagen: {image_path}")
        return []
    
    # Detectar áreas rojas
    red_mask = detect_red_color(image)
    
    # Encontrar contornos de las áreas rojas
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    numbers = []
    
    # Procesar cada contorno
    for contour in contours:
        # Obtener rectángulo delimitador
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filtrar contornos muy pequeños
        if w < 20 or h < 20:
            continue
        
        # Expandir un poco el área para mejor OCR
        padding = 5
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)
        
        # Extraer región de interés
        roi = image[y:y+h, x:x+w]
        
        # Convertir a escala de grises
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Aplicar umbralización
        _, thresh_roi = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Configurar Tesseract para reconocer solo números
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        
        # Realizar OCR
        text = pytesseract.image_to_string(thresh_roi, config=custom_config)
        
        # Limpiar texto extraído
        text = re.sub(r'\D', '', text)  # Eliminar todo lo que no sea dígito
        
        if text and len(text) >= 2:  # Solo aceptar si tiene al menos 2 dígitos
            numbers.append(text)
    
    return numbers

def process_folder(folder_path, output_excel='resultados.xlsx'):
    """
    Procesa todas las imágenes en una carpeta y exporta a Excel
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"La carpeta {folder_path} no existe")
        return
    
    # Extensiones de imagen soportadas
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    # Lista para almacenar resultados
    results = []
    
    # Procesar cada imagen
    for image_file in sorted(folder.iterdir()):
        if image_file.suffix.lower() in image_extensions:
            print(f"Procesando: {image_file.name}")
            
            # Extraer números rojos
            numbers = extract_red_numbers(image_file)
            
            # Obtener nombre base sin extensión
            base_name = image_file.stem
            
            if numbers:
                for number in numbers:
                    results.append({
                        'Archivo': base_name,
                        'Número': number
                    })
                print(f"  -> Encontrados: {numbers}")
            else:
                print(f"  -> No se encontraron números rojos")
    
    # Crear DataFrame
    if results:
        df = pd.DataFrame(results)
        
        # Exportar a Excel
        df.to_excel(output_excel, index=False, sheet_name='Números Rojos')
        print(f"\n✓ Resultados exportados a: {output_excel}")
        print(f"  Total de números encontrados: {len(results)}")
    else:
        print("\n⚠ No se encontraron números rojos en ninguna imagen")

# Ejemplo de uso
if __name__ == "__main__":
    # Configurar la carpeta con las imágenes
    carpeta_imagenes = "input"  # Cambiar por tu ruta
    
    # Procesar las imágenes y generar Excel
    process_folder(carpeta_imagenes, output_excel='numeros_rojos.xlsx')
