# -*- coding: utf-8 -*-
from pdfminer.high_level import extract_text
import pytesseract
from pdf2image import convert_from_path
import logging

# Configura un logger para ver qué motor se está usando
logger = logging.getLogger(__name__)

# Umbral de caracteres para decidir si el texto de pdfminer es útil.
# Si es menor, probablemente es un PDF escaneado o fallido.
MIN_PDFMINER_TEXT_LENGTH = 150 

def _ocr_pdf_with_tesseract(path: str) -> str | None:
    """
    Función 'extra' (fallback) para leer el PDF convirtiéndolo a 
    imágenes y usando Tesseract.
    """
    try:
        # 1. Convertir el PDF (o sus páginas) a una lista de imágenes PIL
        images = convert_from_path(path)
        full_text = []
        
        # 2. Iterar por cada página/imagen y aplicar OCR
        for img in images:
            # Asumimos 'spa' (español) por el contexto de tu proyecto (Chile)
            # y las facturas.
            text_chunk = pytesseract.image_to_string(img, lang='spa') 
            full_text.append(text_chunk)
        
        return "\n".join(full_text) if full_text else None
    
    except Exception as e:
        logger.error(f"Error en el fallback de Tesseract-OCR para {path}: {e}")
        return None

def read_pdf_text(path: str) -> str | None:
    """
    Lee texto de PDF usando una estrategia híbrida (Híbrido PDFMiner + Tesseract):
    
    1. Intenta con PDFMiner (rápido, basado en texto incrustado).
    2. Si falla, o da muy poco texto, usa el fallback ("extra") con 
       Tesseract OCR (lento, pero basado en la imagen visual).
    """
    pdfminer_text = None
    try:
        # --- 1. Intento principal con PDFMiner ---
        pdfminer_text = extract_text(path)
        
        if pdfminer_text and len(pdfminer_text.strip()) > MIN_PDFMINER_TEXT_LENGTH:
            # El texto de PDFMiner parece bueno y suficiente
            logger.info(f"Lectura exitosa con PDFMiner para: {path}")
            return pdfminer_text.strip()
            
    except Exception as e:
        # PDFMiner falló (ej. PDF protegido o corrupto)
        logger.warning(f"PDFMiner falló para {path}. Error: {e}. Intentando Tesseract.")
        pass # Caerá al fallback de Tesseract

    # --- 2. Fallback ("Extra") con Tesseract-OCR ---
    # Esto se activa si pdfminer_text es None, está vacío, o tiene muy 
    # poco contenido (es decir, menor a MIN_PDFMINER_TEXT_LENGTH).
    
    if pdfminer_text:
        logger.warning(f"PDFMiner solo extrajo {len(pdfminer_text.strip())} caracteres. "
                       f"Cambiando a Tesseract-OCR para: {path}")
    else:
        logger.warning(f"PDFMiner no extrajo texto. "
                       f"Cambiando a Tesseract-OCR para: {path}")

    tesseract_text = _ocr_pdf_with_tesseract(path)
    
    if tesseract_text and tesseract_text.strip():
        logger.info(f"Lectura exitosa con Fallback de Tesseract para: {path}")
        return tesseract_text.strip()
    
    logger.error(f"Ambos motores (PDFMiner y Tesseract) fallaron para: {path}")
    return None