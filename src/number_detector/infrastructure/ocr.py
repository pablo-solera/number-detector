from __future__ import annotations

import cv2
import pytesseract

class TesseractService:
    def __init__(self, tesseract_cmd: str):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        self.cfg_digits = "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789"
        self.cfg_motor = "--oem 1 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./-"

    def _prep(self, roi_bgr, scale: float = 2.5):
        roi = cv2.resize(roi_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return th

    def read_digits(self, roi_bgr) -> str:
        th = self._prep(roi_bgr)
        return pytesseract.image_to_string(th, config=self.cfg_digits).strip()

    def read_raw_digits(self, roi_bgr) -> str:
        return pytesseract.image_to_string(roi_bgr,config='--psm 6 -c tessedit_char_whitelist=0123456789')

    def read_text(self, roi_bgr) -> str:
        th = self._prep(roi_bgr)
        return pytesseract.image_to_string(th, config=self.cfg_motor).strip()
