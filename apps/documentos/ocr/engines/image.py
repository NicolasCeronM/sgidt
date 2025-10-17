import cv2
import numpy as np
import logging
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

def _get_perspective_transform(image):
    """
    Encuentra los bordes del documento en la imagen y lo endereza.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    screen_cnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            screen_cnt = approx
            break

    if screen_cnt is None:
        logger.warning("No se pudo detectar un contorno de 4 puntos para la corrección de perspectiva.")
        return image

    pts = screen_cnt.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    (tl, tr, br, bl) = rect
    
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))

    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))

    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]], dtype="float32")

    m = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, m, (max_width, max_height))
    
    return warped


def ocr_from_image_path(image_path: str) -> str:
    """
    Realiza OCR en una imagen, aplicando pre-procesamiento avanzado.
    """
    try:
        img_cv = cv2.imread(image_path)
        if img_cv is None:
            logger.error(f"Error al cargar la imagen desde {image_path}.")
            return ""

        corrected_img = _get_perspective_transform(img_cv)
        gray_img = cv2.cvtColor(corrected_img, cv2.COLOR_BGR2GRAY)
        _, binary_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        custom_config = r'-l spa --oem 3 --psm 6'
        text = pytesseract.image_to_string(binary_img, config=custom_config)
        
        return text

    except Exception as e:
        logger.error(f"Error inesperado durante el OCR: {e}", exc_info=True)
        try:
            return pytesseract.image_to_string(Image.open(image_path), lang='spa')
        except Exception as e_fallback:
            logger.error(f"Fallback a PIL también falló: {e_fallback}")
            return ""