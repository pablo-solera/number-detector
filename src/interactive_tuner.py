"""
Script interactivo para ajustar deteccion de rojo
"""

import cv2
import numpy as np
import pytesseract
from pathlib import Path
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class RedDetectionTuner:
    def __init__(self, image_path):
        self.image = cv2.imread(str(image_path))
        if self.image is None:
            raise ValueError(f"No se pudo cargar la imagen: {image_path}")

        self.image_name = Path(image_path).stem
        self.hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)

        self.h_lower = 0
        self.s_lower = 120
        self.v_lower = 120

        self.window_name = "Red Detection Tuner"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1400, 900)

        self._create_trackbars()

        self.presets = {
            '1': ('Very Loose', 20, 20),
            '2': ('Loose', 50, 50),
            '3': ('Medium', 80, 80),
            '4': ('Strict', 120, 120),
            '5': ('Very Strict', 150, 150)
        }

        print("\n" + "="*70)
        print("RED DETECTION TUNER")
        print("="*70)
        print(f"Image: {image_path}")
        print("\nCONTROLS:")
        print("  Sliders: Adjust S_min and V_min")
        print("  Key 's': Save configuration")
        print("  Key 'r': Reset to defaults")
        print("  Keys 1-5: Load presets")
        for key, (name, s, v) in self.presets.items():
            print(f"    {key} = {name} (S:{s}, V:{v})")
        print("  Key 'q' or ESC: Exit")
        print("="*70 + "\n")

    def _create_trackbars(self):
        cv2.createTrackbar('S_min', self.window_name, self.s_lower, 255, lambda x: None)
        cv2.createTrackbar('V_min', self.window_name, self.v_lower, 255, lambda x: None)

    def get_mask(self):
        self.s_lower = cv2.getTrackbarPos('S_min', self.window_name)
        self.v_lower = cv2.getTrackbarPos('V_min', self.window_name)

        lower_red1 = np.array([self.h_lower, self.s_lower, self.v_lower])
        upper_red1 = np.array([10, 255, 255])

        lower_red2 = np.array([170, self.s_lower, self.v_lower])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(self.hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(self.hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.dilate(mask, kernel, iterations=1)

        return mask

    def detect_numbers(self, mask):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        image_result = self.image.copy()
        numbers = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h

            if area < 180 or w < 18 or h < 12:
                continue

            ratio = w / h
            if ratio < 0.6 or ratio > 6.5:
                continue

            pad_h, pad_v = 19, 12
            x1 = max(x - pad_h, 0)
            y1 = max(y - pad_v, 0)
            x2 = min(x + w + pad_h, self.image.shape[1])
            y2 = min(y + h + pad_v, self.image.shape[0])

            roi = self.image[y1:y2, x1:x2]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            text = pytesseract.image_to_string(thresh,
                                              config="--psm 7 -c tessedit_char_whitelist=0123456789")
            text = text.strip()

            if re.fullmatch(r"\d{3,5}", text):
                numbers.append(text)
                cv2.rectangle(image_result, (x1, y1), (x2, y2), (0, 255, 0), 3)
                # CAMBIO CLAVE: Usar solo str() simple
                cv2.putText(image_result, str(text), (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return image_result, sorted(set(numbers), key=int)

    def create_display(self, mask, result, numbers):
        h, w = self.image.shape[:2]

        scale = 0.45
        new_w, new_h = int(w * scale), int(h * scale)

        img_original = cv2.resize(self.image, (new_w, new_h))
        img_mask = cv2.resize(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), (new_w, new_h))
        img_result = cv2.resize(result, (new_w, new_h))

        info_panel = np.zeros((new_h, 400, 3), dtype=np.uint8)

        y_pos = 40
        line_height = 40

        # TODOS los textos simplificados a ASCII puro
        cv2.putText(info_panel, "CURRENT CONFIG", (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_pos += int(line_height * 1.5)

        cv2.putText(info_panel, "S min: " + str(self.s_lower), (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        y_pos += line_height

        cv2.putText(info_panel, "V min: " + str(self.v_lower), (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        y_pos += int(line_height * 1.5)

        if self.s_lower <= 30:
            level = "VERY LOOSE"
            color = (0, 255, 0)
        elif self.s_lower <= 70:
            level = "LOOSE"
            color = (0, 255, 255)
        elif self.s_lower <= 110:
            level = "MEDIUM"
            color = (0, 165, 255)
        elif self.s_lower <= 140:
            level = "STRICT"
            color = (0, 100, 255)
        else:
            level = "VERY STRICT"
            color = (0, 0, 255)

        cv2.putText(info_panel, "Level: " + level, (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        y_pos += line_height * 2

        cv2.putText(info_panel, "NUMBERS FOUND:", (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_pos += line_height

        if numbers:
            for num in numbers[:10]:
                cv2.putText(info_panel, "  " + str(num), (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                y_pos += line_height
        else:
            cv2.putText(info_panel, "  none", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        y_pos += line_height
        cv2.putText(info_panel, "Total: " + str(len(numbers)), (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row1 = np.hstack([img_original, img_mask])
        row2 = np.hstack([img_result, info_panel])
        display = np.vstack([row1, row2])

        cv2.putText(display, "ORIGINAL", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(display, "MASK", (new_w + 10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(display, "RESULT", (10, new_h + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        return display

    def save_config(self):
        config_file = Path("output/red_detection_config.txt")
        config_file.parent.mkdir(exist_ok=True)

        with open(config_file, 'w') as f:
            f.write(f"# Red detection configuration\n")
            f.write(f"# Generated for: {self.image_name}\n\n")
            f.write(f"RED_LOWER_1 = [0, {self.s_lower}, {self.v_lower}]\n")
            f.write(f"RED_UPPER_1 = [10, 255, 255]\n")
            f.write(f"RED_LOWER_2 = [170, {self.s_lower}, {self.v_lower}]\n")
            f.write(f"RED_UPPER_2 = [180, 255, 255]\n")

        print(f"\nConfiguration saved: {config_file}")
        print(f"   S_min = {self.s_lower}")
        print(f"   V_min = {self.v_lower}\n")

    def load_preset(self, preset_key):
        if preset_key in self.presets:
            name, s, v = self.presets[preset_key]
            cv2.setTrackbarPos('S_min', self.window_name, s)
            cv2.setTrackbarPos('V_min', self.window_name, v)
            print(f"Preset loaded: {name} (S:{s}, V:{v})")

    def run(self):
        while True:
            mask = self.get_mask()
            result, numbers = self.detect_numbers(mask)
            display = self.create_display(mask, result, numbers)

            cv2.imshow(self.window_name, display)

            key = cv2.waitKey(100) & 0xFF

            if key == ord('q') or key == 27:
                print("\nExiting...\n")
                break
            elif key == ord('s'):
                self.save_config()
            elif key == ord('r'):
                cv2.setTrackbarPos('S_min', self.window_name, 120)
                cv2.setTrackbarPos('V_min', self.window_name, 120)
                print("Reset to (120, 120)")
            elif chr(key) in self.presets:
                self.load_preset(chr(key))

        cv2.destroyAllWindows()


def main():
    import sys

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        input_dir = Path("../input")
        images = list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.png"))

        if not images:
            print("No images found in 'input/'")
            print("Usage: python interactive_tuner.py <image_path>")
            return

        image_path = images[0]
        print(f"Using image: {image_path}")

    try:
        tuner = RedDetectionTuner(image_path)
        tuner.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()