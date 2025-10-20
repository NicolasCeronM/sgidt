# apps/documentos/ocr/utils/patterns.py
import re

# Expresión regular mejorada para capturar montos en CLP.
# Captura números con puntos como separadores de miles.
AMOUNT = re.compile(r'\$\s*([\d{1,3}(?:\.\d{3})*])')

# Palabras clave (anclas) para identificar las líneas de los montos.
# Usamos `\b` para asegurar que sean palabras completas.

# --- Patrones existentes que funcionan bien (los mantenemos) ---
RE_FOLIO = re.compile(
    r'(?:\bFOLIO\b\s*[:#]?\s*|N[\u00B0\u00BA]?\s*|NO\.?\s*|#\s*)(\d{1,10})',
    re.IGNORECASE
)
ANCHOR_FACTURA = re.compile(r'\bFACTURA\b', re.IGNORECASE)
ANCHOR_FECHA = re.compile(r'\b(Fecha|Emision)\b', re.IGNORECASE)
RUT_STRICT = r'\b\d{1,2}\.?\d{3}\.?\d{3}\s*-\s*[0-9Kk]\b'
RE_RUT_STRICT = re.compile(RUT_STRICT)


# apps/documentos/ocr/utils/patterns.py
import re








# apps/documentos/ocr/utils/patterns.py
import re

# Regex MEJORADA: Captura montos con '$' o con puntos de miles (evita cantidades como '1')
AMOUNT = re.compile(r'(\$\s*[\d\.]+\d)|(\b\d{1,3}(?:\.\d{3})+\b)')

# Anclas MEJORADAS para incluir los nuevos formatos de etiquetas
ANCHOR_NETO = re.compile(r'\b(MONTO\s+NETO|NETO)\b', re.IGNORECASE)
ANCHOR_EXENTO = re.compile(r'\b(EXENTO)\b', re.IGNORECASE)
ANCHOR_IVA = re.compile(r'\b(IVA|I\.V\.A)\b', re.IGNORECASE)
ANCHOR_TOTAL = re.compile(r'\b(TOTAL)\b', re.IGNORECASE)