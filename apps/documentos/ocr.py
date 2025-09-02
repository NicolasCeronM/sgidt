import os
import re
import mimetypes
import logging
import unicodedata
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple

# Dependencias externas
from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
import pytesseract
from PIL import Image, ImageOps

# =============================================================================
# Configuración y logging
# =============================================================================

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Rutas configurables por entorno (útil en Windows)
_TESSERACT_CMD = os.getenv("TESSERACT_CMD")  # "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
if _TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD

_POPPLER_PATH = os.getenv("POPPLER_PATH")    # "C:\\poppler-24.02.0\\Library\\bin"

# Idiomas y config OCR por defecto
DEFAULT_TESSERACT_LANG = os.getenv("TESSERACT_LANG", "spa+eng")
DEFAULT_TESSERACT_PSM  = os.getenv("TESSERACT_PSM", "6")   # 6 = bloque único de texto
DEFAULT_TESSERACT_OEM  = os.getenv("TESSERACT_OEM", "3")   # 3 = default
DEFAULT_TESSERACT_PSM_IMAGE = os.getenv("TESSERACT_PSM_IMAGE", "4")  # imágenes con layout variable

# =============================================================================
# Regex y constantes
# =============================================================================

# RUT chileno con o sin puntos
RUT_RE = re.compile(r"(?<!\w)(\d{1,2}\.?(?:\d{3}\.)?\d{3}-[\dkK])(?!\w)")
# Folio
FOLIO_RE = re.compile(r"(?:FOLIO|Nº|N°|No\.?|Nro\.?|FOL\.?)[\s:]*([0-9]{3,})", re.IGNORECASE)

# Fechas numéricas: dd[-/.]mm[-/.](yy|yyyy) y yyyy[-/.]mm[-/.]dd
FECHA_RE_NUM = re.compile(
    r"\b(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}|\d{4}[\/\.-]\d{1,2}[\/\.-]\d{1,2})\b"
)

# Fechas con texto: “22 de enero del 2024”, “02 Sep 2025”, “2-SEP-2025”
FECHA_RE_TXT = re.compile(
    r"\b(?P<d>\d{1,2})\s*(?:de|del|-|/)?\s*(?P<m>[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\.]{3,})\.?\s*(?:de|del|-|/)?\s*(?P<y>\d{2,4})\b",
    re.IGNORECASE
)

# Meses (incluye abreviaturas y variantes comunes)
MESES = {
    "enero": 1, "ene": 1,
    "febrero": 2, "feb": 2,
    "marzo": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "mayo": 5, "may": 5,
    "junio": 6, "jun": 6,
    "julio": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "septiembre": 9, "setiembre": 9, "sep": 9, "set": 9,
    "octubre": 10, "oct": 10,
    "noviembre": 11, "nov": 11,
    "diciembre": 12, "dic": 12,
}

# Montos CLP (miles con punto, decimales con coma, signo y $ opcional)
MONEDA_RE = re.compile(r"\$?\s*(-?[0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)")

# Etiquetas de montos típicas
LABELS_MONTOS = {
    "monto_neto":   r"\b(NETO|AFECTO|SUBTOTAL)\b",
    "monto_exento": r"\b(EXENTO)\b",
    "iva":          r"\b(IVA)\b",
    "total":        r"\b(TOTAL)(?:\s+A\s+PAGAR|\s+PAGO)?\b",
}

# Palabras clave para tipo de documento
TIPOS_PALABRAS = {
    "factura_afecta": ["FACTURA ELECTRÓNICA", "FACTURA A", "FACTURA"],
    "factura_exenta": ["FACTURA EXENTA"],
    "boleta_afecta":  ["BOLETA ELECTRÓNICA", "BOLETA"],
    "boleta_exenta":  ["BOLETA EXENTA"],
    "nota_credito":   ["NOTA DE CRÉDITO", "NC ELECTRÓNICA", "NOTA CREDITO"],
}

# Proveedor: etiquetas que suelen preceder al nombre
PROV_KEYS = [
    r"\bRAZ[ÓO]N\s+SOCIAL\b",
    r"\bSE[ÑN]OR(?:ES)?\b",
    r"\bPROVEEDOR(?:A)?\b",
    r"\bEMISOR\b",
    r"\bVENDEDOR\b",
]
PROV_LINEUP_RE = re.compile("|".join(PROV_KEYS), re.IGNORECASE)

# Por si aparece “IVA 19%”
IVA_RATE_RE = re.compile(r"IVA[^0-9%]*(\d{1,2})\s*%")

# =============================================================================
# Utilidades
# =============================================================================

def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s or "")
        if unicodedata.category(c) != "Mn"
    )

def _normalize_amount(s: str) -> Optional[Decimal]:
    """Convierte string chileno ($1.234,56) a Decimal('1234.56')."""
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".").replace(" ", "")
    try:
        return Decimal(s)
    except Exception:
        return None

def _round0(x: Decimal) -> Decimal:
    """Redondeo a entero (sin decimales) típico en CLP."""
    return x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

def _guess_tipo(text: str) -> str:
    up = (text or "").upper()
    for tipo, palabras in TIPOS_PALABRAS.items():
        if any(p in up for p in palabras):
            return tipo
    return "desconocido"

def _guess_iva_rate(text: str) -> Optional[Decimal]:
    m = IVA_RATE_RE.search((text or "").upper())
    if m:
        try:
            return Decimal(m.group(1))
        except Exception:
            return None
    return Decimal("19")  # default Chile

def _preprocess_text(text: str) -> str:
    """Normaliza espacios/caracteres raros y deja todo más parseable."""
    text = (text or "")
    # Espacios no estándar -> espacio normal
    text = text.replace("\u00A0", " ").replace("\u2007", " ").replace("\u202F", " ")
    # Dashes Unicode -> '-'
    text = (text
            .replace("\u2212", "-")
            .replace("\u2010", "-")
            .replace("\u2011", "-")
            .replace("\u2012", "-")
            .replace("\u2013", "-")
            .replace("\u2014", "-"))
    # Normaliza "TOTAL :" / "TOTAL  :" -> "TOTAL:"
    text = text.replace(" :", ":").replace(": ", ": ")
    return text

def _parse_date_numeric(s: str) -> Optional[date]:
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
                "%d-%m-%y", "%d/%m/%y", "%d.%m.%y",
                "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None

def _month_from_text(mtxt: str) -> Optional[int]:
    """Mapea texto de mes a número de mes, tolerante a OCR (enero, Ene, Enro->enero, etc.)."""
    from difflib import get_close_matches
    base = {k: v for k, v in MESES.items()}
    s = _strip_accents(mtxt or "").lower().strip(". ")
    if s in base:
        return base[s]
    # tolerancia por OCR
    cand = get_close_matches(s, base.keys(), n=1, cutoff=0.7)
    return base[cand[0]] if cand else None

def _parse_date_textual(m: re.Match) -> Optional[date]:
    try:
        d = int(m.group("d"))
        y = int(m.group("y"))
        if y < 100:
            y += 2000 if y < 50 else 1900
        month = _month_from_text(m.group("m"))
        if not month:
            return None
        return date(y, month, d)
    except Exception:
        return None

def _extract_first_date(text: str) -> Optional[date]:
    # 1) Numérica directa
    m1 = FECHA_RE_NUM.search(text)
    if m1:
        d = _parse_date_numeric(m1.group(1))
        if d:
            return d
    # 2) Textual (con "de/del" tolerado)
    for m in FECHA_RE_TXT.finditer(text):
        dt = _parse_date_textual(m)
        if dt:
            return dt
    return None

def _montos_en_linea(line: str) -> List[Decimal]:
    return [n for n in (_normalize_amount(m.group(1)) for m in MONEDA_RE.finditer(line)) if n is not None]

def _find_first_pos(text: str, pattern: re.Pattern) -> Optional[int]:
    m = pattern.search(text)
    return m.start() if m else None

def _all_ruts_with_pos(text: str) -> List[Tuple[str, int]]:
    return [(m.group(1), m.start()) for m in RUT_RE.finditer(text)]

def _select_proveedor_rut(text: str) -> Optional[str]:
    """
    Selecciona el RUT del PROVEEDOR:
    - Prefiere RUTs ubicados ANTES del bloque 'SEÑOR(ES)' (cliente).
    - Si hay 'FACTURA/BOLETA/NOTA' arriba, prioriza RUT por encima.
    - Si hay varios, toma el más superior.
    """
    ruts = _all_ruts_with_pos(text)
    if not ruts:
        return None

    up = text.upper()
    pos_senor = _find_first_pos(up, re.compile(r"\bSE[ÑN]OR(?:ES)?\b"))
    pos_fact = _find_first_pos(up, re.compile(r"\b(FACTURA|BOLETA|NOTA)\b"))

    candidatos = ruts
    if pos_senor is not None:
        candidatos = [rp for rp in candidatos if rp[1] < pos_senor] or candidatos

    if pos_fact is not None:
        arriba = [rp for rp in candidatos if rp[1] <= pos_fact]
        if arriba:
            candidatos = arriba

    candidatos.sort(key=lambda x: x[1])
    return candidatos[0][0] if candidatos else None

def _pretty_name(s: str) -> str:
    s = s.strip()
    # Quita RUT si viene pegado
    s = re.sub(RUT_RE, "", s).strip(" -:|")
    s = re.sub(r"\s{2,}", " ", s)
    if s.isupper():
        sc = s.title()
        sc = re.sub(r"\b(Spa|Ltda|Eirl|E\.I\.R\.L|Eirl\.|S\.A\.?)\b", lambda m: m.group(0).upper(), sc)
        return sc
    return s

def _extract_proveedor(lines: List[str], rut: Optional[str]) -> Optional[str]:
    """
    Heurística para nombre de proveedor:
      - Busca etiquetas (Razón Social, Emisor, Vendedor).
      - Evita bloque 'SEÑOR(ES)' (cliente).
      - Si tenemos rut del proveedor, busca líneas cercanas arriba.
      - Si no, busca en encabezado (primeras ~15 líneas) cadenas tipo razón social.
    """
    joined = "\n".join(lines)
    pos_senor = _find_first_pos(joined.upper(), re.compile(r"\bSE[ÑN]OR(?:ES)?\b"))
    cut_index = None
    if pos_senor is not None:
        # Determina línea de inicio de 'SEÑOR(ES)' para cortar búsqueda hacia abajo
        acc = 0
        for i, ln in enumerate(lines):
            acc += len(ln) + 1
            if acc >= pos_senor:
                cut_index = i
                break
    search_range = lines[:cut_index] if cut_index else lines

    # 1) Por etiquetas
    for i, ln in enumerate(search_range):
        if PROV_LINEUP_RE.search(ln):
            after = ln.split(":")[-1].strip()
            cand = after or (search_range[i+1].strip() if i+1 < len(search_range) else "")
            cand = re.sub(r"[\*\#\|]+", " ", cand).strip()
            cand = re.sub(r"\s{2,}", " ", cand)
            if cand and len(cand) > 2:
                return _pretty_name(cand)

    # 2) Cercano al rut del proveedor
    if rut:
        rut_clean = rut.replace(".", "")
        idx_rut = None
        for i, ln in enumerate(search_range):
            if rut_clean in ln.replace(".", ""):
                idx_rut = i
                break
        if idx_rut is not None:
            for j in range(max(0, idx_rut-3), idx_rut+1):
                cand = search_range[j].strip()
                if len(cand) > 3 and not re.search(r"\b(FACTURA|BOLETA|NOTA|RUT|FOLIO|SII|ELECTR[ÓO]NICA)\b", cand, re.IGNORECASE):
                    return _pretty_name(cand)

    # 3) Encabezado (primeras 15 líneas)
    for cand in search_range[:15]:
        c = cand.strip()
        if len(c) >= 6 and (c.isupper() or " SPA" in c or " LTDA" in c or " S.A" in c):
            if not re.search(r"\b(FACTURA|BOLETA|NOTA|RUT|FOLIO|SII|ELECTR[ÓO]NICA)\b", c, re.IGNORECASE):
                return _pretty_name(c)

    return None

def _parse_montos(text: str, tipo: str, iva_rate: Decimal) -> Dict[str, Optional[Decimal]]:
    """
    Extrae montos (neto, exento, iva, total) tolerando saltos de línea y variaciones.
    Aplica heurísticas para Nota de Crédito (signo) y recalcula faltantes.
    """
    campos: Dict[str, Optional[Decimal]] = {"monto_neto": None, "monto_exento": None, "iva": None, "total": None}

    lines = text.splitlines()
    U = [ln.upper() for ln in lines]

    # 1) Por etiquetas
    for key, pat in LABELS_MONTOS.items():
        if campos[key] is not None:
            continue
        regex = re.compile(pat, re.IGNORECASE)
        for idx, up in enumerate(U):
            if regex.search(up):
                candidatos: List[Decimal] = []
                for j in range(idx, min(idx + 3, len(lines))):
                    candidatos += _montos_en_linea(lines[j])
                if candidatos:
                    campos[key] = max(candidatos, key=lambda z: abs(z))
                break

    # 2) Fallback global (total suele ser el mayor |valor|)
    todos = [n for n in (_normalize_amount(m.group(1)) for m in MONEDA_RE.finditer(text)) if n is not None]
    if campos["total"] is None and todos:
        campos["total"] = max(todos, key=lambda z: abs(z))

    # 3) Derivar IVA si falta y tenemos total + neto/exento
    if campos["total"] is not None and campos["iva"] is None:
        neto   = campos["monto_neto"]
        exento = campos["monto_exento"] or Decimal("0")
        if neto is not None:
            posible_iva = campos["total"] - neto - exento
            if abs(posible_iva) < Decimal("1"):
                posible_iva = (neto * iva_rate / Decimal("100")).quantize(Decimal("1"))
            campos["iva"] = posible_iva if posible_iva != 0 else None

    # 4) Derivar neto si falta
    if campos["monto_neto"] is None and campos["total"] is not None:
        exento = campos["monto_exento"] or Decimal("0")
        if campos["iva"] is not None:
            campos["monto_neto"] = campos["total"] - exento - campos["iva"]
        else:
            neto_est = (campos["total"] - exento) / (Decimal("1") + (iva_rate/Decimal("100")))
            campos["monto_neto"] = _round0(neto_est)
            iva_est = campos["total"] - exento - campos["monto_neto"]
            campos["iva"] = iva_est if abs(iva_est) > 0 else None

    # 5) Ajuste de signo para Nota de Crédito
    if tipo.startswith("nota_credito"):
        for k in ["monto_neto", "monto_exento", "iva", "total"]:
            v = campos[k]
            if v is not None and v > 0:
                campos[k] = -v

    # 6) Redondeos a CLP (enteros) para neto/iva/total
    for k in ["monto_neto", "iva", "total"]:
        v = campos[k]
        if v is not None:
            campos[k] = _round0(v)

    # 7) Consistencia (tolerancia OCR)
    tol = Decimal("2")
    neto = campos["monto_neto"] or Decimal("0")
    exento = campos["monto_exento"] or Decimal("0")
    iva = campos["iva"] or Decimal("0")
    total = campos["total"]
    if total is not None:
        diff = total - (neto + exento + iva)
        if abs(diff) <= tol:
            campos["iva"] = _round0(iva + diff)

    return campos

# =============================================================================
# Extracción de texto (PDF/Imagen)
# =============================================================================

def _text_from_pdf(path: str) -> str:
    """Intenta extraer texto del PDF; si no hay, usa OCR (pdf2image + tesseract)."""
    try:
        text = extract_text(path) or ""
        if len(text.strip()) > 40:
            logger.debug("Texto obtenido desde capa de texto del PDF.")
            return text
    except Exception as e:
        logger.warning(f"Fallo extract_text PDF: {e}")

    # Fallback OCR
    try:
        images = convert_from_path(path, fmt="png", dpi=300, poppler_path=_POPPLER_PATH)
        ocr_texts = []
        for im in images:
            im = ImageOps.exif_transpose(im)
            ocr_texts.append(
                pytesseract.image_to_string(
                    im,
                    lang=DEFAULT_TESSERACT_LANG,
                    config=f"--psm {DEFAULT_TESSERACT_PSM} --oem {DEFAULT_TESSERACT_OEM}"
                )
            )
        logger.debug("Texto extraído por OCR desde PDF rasterizado.")
        return "\n".join(ocr_texts)
    except Exception as e:
        logger.error(f"Fallo OCR PDF: {e}")
        return ""

def _text_from_imagefile(path: str) -> str:
    """Extrae texto OCR desde imagen JPG/PNG."""
    try:
        im = Image.open(path)
        im = ImageOps.exif_transpose(im)  # Corrige orientación
        return pytesseract.image_to_string(
            im,
            lang=DEFAULT_TESSERACT_LANG,
            config=f"--psm {DEFAULT_TESSERACT_PSM_IMAGE} --oem {DEFAULT_TESSERACT_OEM}",
        )
    except Exception as e:
        logger.error(f"Fallo OCR imagen: {e}")
        return ""

# =============================================================================
# API pública
# =============================================================================

@dataclass
class OCRResult:
    raw_text: str
    rut_proveedor: str = ""
    proveedor_nombre: str = ""
    folio: str = ""
    fecha_emision: Optional[date] = None
    tipo_documento: str = "desconocido"
    iva_tasa: Optional[Decimal] = None
    monto_neto: Optional[Decimal] = None
    monto_exento: Optional[Decimal] = None
    iva: Optional[Decimal] = None
    total: Optional[Decimal] = None
    fuente_texto: str = "desconocido"  # "pdf_text", "pdf_ocr", "image_ocr"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Serializa Decimal a str para JSON-friendly
        for k in ["iva_tasa", "monto_neto", "monto_exento", "iva", "total"]:
            v = data.get(k)
            if isinstance(v, Decimal):
                data[k] = str(v)
        return data

def parse_text(text: str) -> OCRResult:
    """Parses sobre un texto crudo (útil para tests)."""
    raw = _preprocess_text(text or "")
    tipo = _guess_tipo(raw)
    iva_rate = _guess_iva_rate(raw) or Decimal("19")

    # ---- RUT del proveedor (robusto) ----
    rut = _select_proveedor_rut(raw)
    if rut:
        rut = rut.replace(".", "").upper()

    # ---- Folio ----
    folio = None
    m_f = FOLIO_RE.search(raw)
    if m_f:
        folio = m_f.group(1)

    # ---- Fecha ----
    fecha = _extract_first_date(raw)

    # ---- Proveedor (razón social) ----
    proveedor_nombre = _extract_proveedor(raw.splitlines(), rut)

    # ---- Montos ----
    montos = _parse_montos(raw, tipo, iva_rate)

    return OCRResult(
        raw_text=raw,
        rut_proveedor=rut or "",
        proveedor_nombre=proveedor_nombre or "",
        folio=folio or "",
        fecha_emision=fecha,
        tipo_documento=tipo,
        iva_tasa=iva_rate,
        **montos,
        fuente_texto="unknown",
    )

def parse_file(path: str, mime: Optional[str] = None) -> Dict[str, Any]:
    """
    Dado un archivo PDF/JPG/PNG retorna dict con datos clave extraídos.
    - Si es PDF: intenta capa de texto; si no hay, OCR.
    - Si es imagen: OCR con PSM para imágenes.
    - Heurísticas robustas para proveedor, fecha y montos.
    """
    mime = mime or mimetypes.guess_type(path)[0] or ""

    if mime.startswith("application/pdf") or path.lower().endswith(".pdf"):
        text = _text_from_pdf(path)
        fuente = "pdf_text" if len(text.strip()) > 40 else "pdf_ocr"
    elif mime.startswith("image/"):
        text = _text_from_imagefile(path)
        fuente = "image_ocr"
    else:
        if path.lower().endswith(".pdf"):
            text = _text_from_pdf(path)
            fuente = "pdf_text" if len(text.strip()) > 40 else "pdf_ocr"
        else:
            text = ""
            fuente = "unknown"

    result = parse_text(text)
    result.fuente_texto = fuente

    logger.info(
        f"OCR parse_file: tipo={result.tipo_documento}, rut={result.rut_proveedor}, "
        f"folio={result.folio}, fecha={result.fecha_emision}, total={result.total}"
    )

    return result.to_dict()

# =============================================================================
# CLI simple para pruebas locales:
#   python ocr_enhanced.py <ruta_archivo>
# =============================================================================

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Uso: python ocr_enhanced.py <ruta_archivo>")
        sys.exit(1)
    path = sys.argv[1]
    out = parse_file(path)
    print(json.dumps(out, ensure_ascii=False, indent=2))
