import fitz
import pytesseract
from PIL import Image, ImageEnhance
import cv2
import numpy as np
import logging
from spellchecker import SpellChecker

logger = logging.getLogger(__name__)

class DocumentReader:
    def __init__(self):
        self.needs_ocr = False
        self.spell_checker = SpellChecker()

    def read(self, file_path: str) -> str:
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                page_text = page.get_text()
                
                if not page_text.strip():
                    self.needs_ocr = True
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img = self.enhance_image(img)
                    page_text = self.perform_ocr(img)
                
                text += page_text + "\n"
            
            doc.close()
            return self.postprocess_ocr(text)
        except Exception as e:
            logger.error(f"Error reading document: {e}")
            return ""

    def enhance_image(self, img: Image) -> Image:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        return img

    def perform_ocr(self, img: Image) -> str:
        try:
            tesseract_text = pytesseract.image_to_string(img)
            
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            cv_img = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            cv_text = pytesseract.image_to_string(cv_img)
            
            combined_text = tesseract_text + " " + cv_text
            return combined_text
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""

    def postprocess_ocr(self, text: str) -> str:
        return self.spell_checker.correction(text)