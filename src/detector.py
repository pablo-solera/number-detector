import cv2
import numpy as np
import pytesseract
import re
from pathlib import Path
import config

if config.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


class RedNumberDetector:
    def __init__(self):
        self.red_lower_1 = np.array(config.RED_LOWER_1)
        self.red_upper_1 = np.array(config.RED_UPPER_1)
        self.red_lower_2 = np.array(config.RED_LOWER_2)
        self.red_upper_2 = np.array(config.RED_UPPER_2)
    
    def detect_red_color(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        mask1 = cv2.inRange(hsv, self.red_lower_1, self.red_upper_1)
        mask2 = cv2.inRange(hsv, self.red_lower_2, self.red_upper_2)
        
        red_mask = cv2.bitwise_or(mask1, mask2)
        
        kernel = np.ones((3, 3), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
        
        return red_mask
    
    def extract_numbers_from_roi(self, roi):
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh_roi = cv2.threshold(gray_roi, 0, 255, 
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        text = pytesseract.image_to_string(thresh_roi, 
                                          config=config.TESSERACT_CONFIG)
        
        text = re.sub(r'\D', '', text)
        
        if text and len(text) >= config.MIN_DIGITS:
            return text
        return None
    
    def extract_red_numbers(self, image_path):
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"Error al leer la imagen: {image_path}")
            return []
        
        red_mask = self.detect_red_color(image)
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        numbers = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            if w < config.MIN_CONTOUR_WIDTH or h < config.MIN_CONTOUR_HEIGHT:
                continue
            
            padding = config.CONTOUR_PADDING
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(image.shape[1] - x, w + 2 * padding)
            h = min(image.shape[0] - y, h + 2 * padding)
            
            roi = image[y:y+h, x:x+w]
            number = self.extract_numbers_from_roi(roi)
            
            if number:
                numbers.append(number)
        
        return numbers
    
    def process_folder(self, folder_path):
        folder = Path(folder_path)
        
        if not folder.exists():
            raise FileNotFoundError(f"La carpeta {folder_path} no existe")
        
        results = []
        
        for image_file in sorted(folder.iterdir()):
            if image_file.suffix.lower() in config.IMAGE_EXTENSIONS:
                print(f"Procesando: {image_file.name}")
                
                numbers = self.extract_red_numbers(image_file)
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
        
        return results
