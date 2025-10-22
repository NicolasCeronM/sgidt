# apps/documentos/ocr/engines/image.py
import cv2
import numpy as np
import logging
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

def ocr_from_image_path(image_path: str) -> str:
    """
    Realiza OCR en una imagen utilizando un pipeline de pre-procesamiento profesional.
    """
    try:
        # 1. Cargar la imagen con OpenCV
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Error al cargar la imagen desde la ruta: {image_path}")
            return ""

        # --- Pipeline de Pre-procesamiento ---

        # 2. Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 3. Redimensionar para mejorar la resolución (opcional pero recomendado)
        # Apuntamos a una altura de ~1000-1200px que suele funcionar bien
        scale_factor = 1200 / gray.shape[0]
        if scale_factor > 1:
            gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

        # 4. Eliminar ruido con un filtro de mediana
        # Es muy efectivo contra el ruido "sal y pimienta" de las fotos
        denoised = cv2.medianBlur(gray, 3)

        # 5. Binarización de Otsu: La clave para un buen contraste
        # Calcula automáticamente el umbral óptimo para separar texto y fondo.
        _, binary_img = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # --- Fin del Pipeline ---

        # 6. Configuración de Tesseract optimizada para facturas
        # --psm 3: Totalmente automático, deja que Tesseract decida la estructura. Es el más robusto.
        custom_config = r'-l spa --oem 3 --psm 3'
        
        # 7. Extraer texto usando Tesseract
        text = pytesseract.image_to_string(binary_img, config=custom_config)
        
        return text

    except Exception as e:
        logger.error(f"Error inesperado durante el OCR de la imagen: {e}", exc_info=True)
        # Fallback por si OpenCV falla por alguna razón
        try:
            return pytesseract.image_to_string(Image.open(image_path), lang='spa')
        except Exception as e_fallback:
            logger.error(f"El OCR de fallback también falló: {e_fallback}")
            return ""