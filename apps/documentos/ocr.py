import re
import mimetypes
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
import pytesseract
from PIL import Image

# -------------------------------------------------------------------
# Regex principales
# -------------------------------------------------------------------
RUT_RE = re.compile(r"\b(\d{1,2}\.?(?:\d{3}\.)?\d{3}-[\dkK])\b")
FOLIO_RE = re.compile(r"(?:FOLIO|Nº|N°|No\.?)[\s:]*([0-9]{3,})", re.IGNORECASE)

# Acepta dd-mm-YYYY, dd/mm/YYYY, dd-mm-YY, dd/mm/YY y también YYYY-mm-dd, YYYY/mm/dd
FECHA_RE = re.compile(
    r"\b(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}|\d{4}[\/-]\d{1,2}[\/-]\d{1,2})\b"
)

# Montos con signo opcional, miles con punto y decimales con coma
MONEDA_RE = re.compile(r"\$?\s*(-?[0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)")

# Palabras clave para tipo de documento
TIPOS_PALABRAS = {
    "factura_afecta": ["FACTURA ELECTRÓNICA", "FACTURA"],
    "factura_exenta": ["FACTURA EXENTA"],
    "boleta_afecta": ["BOLETA ELECTRÓNICA", "BOLETA"],
    "boleta_exenta": ["BOLETA EXENTA"],
    "nota_credito": ["NOTA DE CRÉDITO"],
}

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _normalize_amount(s: str) -> Decimal | None:
    """Convierte string chileno ($1.234,56) a Decimal."""
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        return None


def _guess_tipo(text: str) -> str:
    up = text.upper()
    for tipo, palabras in TIPOS_PALABRAS.items():
        if any(p in up for p in palabras):
            return tipo
    return "desconocido"


def _preprocess_text(text: str) -> str:
    """Normaliza espacios/caracteres raros y deja todo más parseable."""
    # Espacios no estándar -> espacio normal
    text = (text or "").replace("\u00A0", " ").replace("\u2007", " ").replace("\u202F", " ")
    # Guiones/dashes y "minus" Unicode -> hyphen ASCII
    text = (text
            .replace("\u2212", "-")   # minus sign
            .replace("\u2010", "-")   # hyphen
            .replace("\u2011", "-")   # non-breaking hyphen
            .replace("\u2012", "-")   # figure dash
            .replace("\u2013", "-")   # en dash
            .replace("\u2014", "-"))  # em dash
    # Normaliza "TOTAL :" / "TOTAL  :" -> "TOTAL:"
    text = text.replace(" :", ":").replace(": ", ": ")
    return text


def _round0(x: Decimal) -> Decimal:
    """Redondeo a entero (sin decimales) como suele ocurrir en CLP."""
    return x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _parse_montos(text: str) -> dict:
    """Extrae montos (neto, exento, iva, total) desde el texto, tolerando saltos de línea y (19%)."""
    campos = {"monto_neto": None, "monto_exento": None, "iva": None, "total": None}

    # Utilidad: extrae TODOS los montos con formato moneda de una línea
    def montos_en_linea(line: str):
        return [_normalize_amount(m.group(1)) for m in MONEDA_RE.finditer(line)]

    # 1) Busca por etiquetas, permitiendo que el número esté en la misma línea o en las 2 siguientes
    LABELS = {
        "monto_neto": r"\bNETO\b",
        "monto_exento": r"\bEXENTO\b",
        "iva": r"\bIVA\b",
        "total": r"\bTOTAL\b(?:\s+A\s+PAGAR|\s+PAGO)?",
    }
    lines = text.splitlines()
    U = [ln.upper() for ln in lines]

    for key, pat in LABELS.items():
        if campos[key] is not None:
            continue
        for idx, up in enumerate(U):
            if re.search(pat, up, re.I):
                # Junta montos de la línea de la etiqueta y de las 2 siguientes
                candidatos = []
                for j in range(idx, min(idx + 3, len(lines))):
                    candidatos += [n for n in montos_en_linea(lines[j]) if n is not None]
                if candidatos:
                    # Para TOTAL elegimos el mayor; para IVA/NETO/EXENTO tomamos el primero “razonable”
                    if key == "total":
                        campos[key] = max(candidatos, key=lambda z: abs(z))
                    else:
                        # Elige el valor con mayor |z|, evita confundir “19%” (no tiene formato moneda)
                        campos[key] = max(candidatos, key=lambda z: abs(z))
                break  # seguimos con la próxima etiqueta

    # 2) Fallbacks globales con todos los montos del documento
    todos = [_normalize_amount(m.group(1)) for m in MONEDA_RE.finditer(text)]
    todos = [n for n in todos if n is not None]

    # Total: si no lo obtuvimos por etiqueta, el de mayor |valor| suele ser el total (o el de la NC)
    if campos["total"] is None and todos:
        campos["total"] = max(todos, key=lambda z: abs(z))

    # IVA: si falta y tenemos total + (neto o exento), derivarlo
    if campos["total"] is not None and campos["iva"] is None:
        neto   = campos["monto_neto"]
        exento = campos["monto_exento"] or Decimal("0")
        if neto is not None:
            posible_iva = campos["total"] - neto - exento
            campos["iva"] = posible_iva if posible_iva != 0 else None

    # Neto: si falta y hay total + otros montos, elegir uno < |total| y cercano en valor absoluto
    if campos["total"] is not None and campos["monto_neto"] is None and todos:
        candidatos = [n for n in todos if n != campos["total"] and abs(n) < abs(campos["total"])]
        if candidatos:
            campos["monto_neto"] = max(candidatos, key=lambda z: abs(z))

    # Estimación final si aún faltan neto e IVA (asumiendo 19%)
    if campos["total"] is not None and campos["monto_neto"] is None and campos["iva"] is None:
        neto_est = (campos["total"] / Decimal("1.19")).quantize(Decimal("1"))
        iva_est  = campos["total"] - neto_est
        campos["monto_neto"] = neto_est
        campos["iva"] = iva_est if iva_est != 0 else None

    return campos




def _text_from_pdf(path: str) -> str:
    """Extrae texto desde PDF (primero capa de texto, luego OCR si es necesario)."""
    try:
        text = extract_text(path) or ""
        if len(text.strip()) > 40:  # si hay suficiente texto
            return text
    except Exception:
        pass

    # Fallback OCR
    try:
        images = convert_from_path(path, fmt="png", dpi=300)
        ocr_texts = []
        for im in images:
            ocr_texts.append(pytesseract.image_to_string(im, lang="spa", config="--psm 6"))
        return "\n".join(ocr_texts)
    except Exception:
        return ""


def _text_from_imagefile(path: str) -> str:
    """Extrae texto OCR desde imagen JPG/PNG."""
    im = Image.open(path)
    return pytesseract.image_to_string(im, lang="spa", config="--psm 6")


# -------------------------------------------------------------------
# Punto de entrada principal
# -------------------------------------------------------------------
def parse_file(path: str, mime: str | None = None) -> dict:
    """Dado un archivo PDF/JPG/PNG retorna dict con datos clave extraídos."""
    mime = mime or mimetypes.guess_type(path)[0] or ""

    if mime.startswith("application/pdf"):
        text = _text_from_pdf(path)
    elif mime.startswith("image/"):
        text = _text_from_imagefile(path)
    else:
        if path.lower().endswith(".pdf"):
            text = _text_from_pdf(path)
        else:
            text = ""

    raw = text or ""
    raw = _preprocess_text(raw)

    # --- Extracciones básicas ---
    rut = None
    m_rut = RUT_RE.search(raw)
    if m_rut:
        rut = m_rut.group(1).replace(".", "").upper()

    folio = None
    m_f = FOLIO_RE.search(raw)
    if m_f:
        folio = m_f.group(1)

    fecha = None
    m_fecha = FECHA_RE.search(raw)
    if m_fecha:
        s = m_fecha.group(1)
        # Probar varios formatos comunes (incluye YYYY-mm-dd)
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                fecha = datetime.strptime(s, fmt).date()
                break
            except Exception:
                pass

    tipo = _guess_tipo(raw)
    montos = _parse_montos(raw)

    return {
        "raw_text": raw,
        "rut_proveedor": rut or "",
        "folio": folio or "",
        "fecha_emision": fecha,
        "tipo_documento": tipo,
        **montos,
    }
