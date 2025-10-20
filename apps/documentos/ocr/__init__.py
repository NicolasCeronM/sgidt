# apps/documentos/ocr/__init__.py

"""
Módulo de procesamiento de documentos (OCR y extracción de datos).

Este __init__.py actúa como la fachada principal del módulo, exponiendo
la función 'parse_document' del orquestador 'parsing.py' como la
entrada principal para el resto de la aplicación.
"""

from .parsing import parse_document

__all__ = ["parse_document"]