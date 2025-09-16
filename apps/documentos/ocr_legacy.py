# -*- coding: utf-8 -*-
"""
OCR robusto para DTE CL (PDF/JPG/PNG)
- RUT tolerante a espacios tras guion (e.g., "15.608.506- 5")
- Montos por cercanía a etiquetas con ventana amplia
- Filtro anti-RUT para valores monetarios
- Derivación de IVA/NETO con tolerancia y redondeo
- Fallback OCR con preprocesamiento ligero
"""
import os
import re
import mimetypes
import logging
import unicodedata
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple

# OCR / PDF
from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
import pytesseract
from PIL import Image, ImageOps, ImageFilter

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Opcionales para Windows
_TESSERACT_CMD = os.getenv("TESSERACT_CMD")  # p.ej. "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
if _TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD
_POPPLER_PATH = os.getenv("POPPLER_PATH")    # p.ej. "C:\\poppler-24.02.0\\Library\\bin"

DEFAULT_TESSERACT_LANG = os.getenv("TESSERACT_LANG", "spa+eng")
DEFAULT_TESSERACT_PSM  = os.getenv("TESSERACT_PSM", "6")
DEFAULT_TESSERACT_OEM  = os.getenv("TESSERACT_OEM", "3")
DEFAULT_TESSERACT_PSM_IMAGE = os.getenv("TESSERACT_PSM_IMAGE", "4")

# -----------------------------------------------------------------------------
# Regex y constantes
# -----------------------------------------------------------------------------
# Acepta espacios después del guion del DV
RUT_RE = re.compile(r"(?<!\w)(\d{1,2}\.?(?:\d{3}\.)?\d{3})-\s*([\dkK])(?!\w)")
FOLIO_RE = re.compile(r"(?:FOLIO|Nº|N°|No\.?|Nro\.?|FOL\.?)[\s:]*([0-9]{3,})", re.IGNORECASE)

FECHA_RE_NUM = re.compile(r"\b(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}|\d{4}[\/\.-]\d{1,2}[\/\.-]\d{1,2})\b")
FECHA_RE_TXT = re.compile(
    r"\b(?P<d>\d{1,2})\s*(?:de|del|-|/)?\s*(?P<m>[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\.]{3,})\.?\s*(?:de|del|-|/)?\s*(?P<y>\d{2,4})\b",
    re.IGNORECASE
)

MESES = {
    "enero":1,"ene":1,"febrero":2,"feb":2,"marzo":3,"mar":3,"abril":4,"abr":4,"mayo":5,"may":5,
    "junio":6,"jun":6,"julio":7,"jul":7,"agosto":8,"ago":8,"septiembre":9,"setiembre":9,"sep":9,"set":9,
    "octubre":10,"oct":10,"noviembre":11,"nov":11,"diciembre":12,"dic":12,
}

MONEDA_RE = re.compile(r"\$?\s*(-?[0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)")

LABELS_MONTOS = {
    "monto_neto":   r"\b(NETO|AFECTO|SUBTOTAL)\b",
    "monto_exento": r"\b(EXENTO)\b",
    "iva":          r"\b(I\.?V\.?A\.?|IVA)\b",
    "total":        r"\b(TOTAL)(?:\s+A\s+PAGAR|\s+PAGO)?\b",
}

TIPOS_PALABRAS = {
    "factura_afecta": ["FACTURA ELECTRÓNICA", "FACTURA A", "FACTURA"],
    "factura_exenta": ["FACTURA EXENTA"],
    "boleta_afecta":  ["BOLETA ELECTRÓNICA", "BOLETA"],
    "boleta_exenta":  ["BOLETA EXENTA"],
    "nota_credito":   ["NOTA DE CRÉDITO", "NC ELECTRÓNICA", "NOTA CREDITO"],
}

PROV_KEYS = [
    r"\bRAZ[ÓO]N\s+SOCIAL\b",
    r"\bSE[ÑN]OR(?:ES)?\b",
    r"\bPROVEEDOR(?:A)?\b",
    r"\bEMISOR\b",
    r"\bVENDEDOR\b",
]
PROV_LINEUP_RE = re.compile("|".join(PROV_KEYS), re.IGNORECASE)
IVA_RATE_RE = re.compile(r"IVA[^0-9%]*(\d{1,2})\s*%")

# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------
def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")

def _normalize_amount(s: str) -> Optional[Decimal]:
    if not s: return None
    s = s.replace(".", "").replace(",", ".").replace(" ", "")
    try: return Decimal(s)
    except Exception: return None

def _round0(x: Decimal) -> Decimal:
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
        try: return Decimal(m.group(1))
        except Exception: return None
    return Decimal("19")

def _preprocess_text(text: str) -> str:
    text = (text or "")
    text = text.replace("\u00A0", " ").replace("\u2007", " ").replace("\u202F", " ")
    text = (text.replace("\u2212","-").replace("\u2010","-").replace("\u2011","-")
                 .replace("\u2012","-").replace("\u2013","-").replace("\u2014","-"))
    text = text.replace(" :", ":").replace(": ", ": ")
    return text

def _parse_date_numeric(s: str) -> Optional[date]:
    for fmt in ("%d-%m-%Y","%d/%m/%Y","%d.%m.%Y","%d-%m-%y","%d/%m/%y","%d.%m.%y","%Y-%m-%d","%Y/%m/%d","%Y.%m.%d"):
        try: return datetime.strptime(s, fmt).date()
        except Exception: continue
    return None

def _month_from_text(mtxt: str) -> Optional[int]:
    from difflib import get_close_matches
    s = _strip_accents(mtxt or "").lower().strip(". ")
    if s in MESES: return MESES[s]
    cand = get_close_matches(s, MESES.keys(), n=1, cutoff=0.7)
    return MESES[cand[0]] if cand else None

def _parse_date_textual(m: re.Match) -> Optional[date]:
    try:
        d = int(m.group("d")); y = int(m.group("y")); y = y+2000 if y<50 else (y+1900 if y<100 else y)
        month = _month_from_text(m.group("m"))
        return date(y, month, d) if month else None
    except Exception:
        return None

def _extract_first_date(text: str) -> Optional[date]:
    m1 = FECHA_RE_NUM.search(text)
    if m1:
        d = _parse_date_numeric(m1.group(1))
        if d: return d
    for m in FECHA_RE_TXT.finditer(text):
        dt = _parse_date_textual(m)
        if dt: return dt
    return None

def _montos_en_linea(line: str) -> List[Decimal]:
    return [n for n in (_normalize_amount(m.group(1)) for m in MONEDA_RE.finditer(line)) if n is not None]

def _find_first_pos(text: str, pattern: re.Pattern) -> Optional[int]:
    m = pattern.search(text); return m.start() if m else None

def _all_ruts_with_pos(text: str) -> List[Tuple[str, int]]:
    outs = []
    for m in RUT_RE.finditer(text):
        cuerpo, dv = m.group(1), m.group(2)
        rut = f"{cuerpo}-{dv}".replace(" ", "")
        outs.append((rut, m.start()))
    return outs

def _select_proveedor_rut(text: str) -> Optional[str]:
    ruts = _all_ruts_with_pos(text)
    if not ruts: return None
    up = text.upper()
    pos_senor = _find_first_pos(up, re.compile(r"\bSE[ÑN]OR(?:ES)?\b"))
    pos_fact = _find_first_pos(up, re.compile(r"\b(FACTURA|BOLETA|NOTA)\b"))
    candidatos = ruts
    if pos_senor is not None:
        candidatos = [rp for rp in candidatos if rp[1] < pos_senor] or candidatos
    if pos_fact is not None:
        arriba = [rp for rp in candidatos if rp[1] <= pos_fact]
        if arriba: candidatos = arriba
    candidatos.sort(key=lambda x: x[1])
    return candidatos[0][0] if candidatos else None

def _pretty_name(s: str) -> str:
    s = s.strip()
    s = re.sub(RUT_RE, "", s).strip(" -:|")
    s = re.sub(r"\s{2,}", " ", s)
    if s.isupper():
        sc = s.title()
        sc = re.sub(r"\b(Spa|Ltda|Eirl|E\.I\.R\.L|Eirl\.|S\.A\.?)\b", lambda m: m.group(0).upper(), sc)
        return sc
    return s

def _extract_proveedor(lines: List[str], rut: Optional[str]) -> Optional[str]:
    joined = "\n".join(lines)
    pos_senor = _find_first_pos(joined.upper(), re.compile(r"\bSE[ÑN]OR(?:ES)?\b"))
    cut_index = None
    if pos_senor is not None:
        acc = 0
        for i, ln in enumerate(lines):
            acc += len(ln) + 1
            if acc >= pos_senor:
                cut_index = i; break
    search_range = lines[:cut_index] if cut_index else lines

    for i, ln in enumerate(search_range):
        if PROV_LINEUP_RE.search(ln):
            after = ln.split(":")[-1].strip()
            cand = after or (search_range[i+1].strip() if i+1 < len(search_range) else "")
            cand = re.sub(r"[\*\#\|]+"," ", cand).strip()
            cand = re.sub(r"\s{2,}"," ", cand)
            if len(cand) > 2:
                return _pretty_name(cand)

    if rut:
        rut_clean = rut.replace(".", "")
        idx_rut = None
        for i, ln in enumerate(search_range):
            if rut_clean in ln.replace(".", ""):
                idx_rut = i; break
        if idx_rut is not None:
            for j in range(max(0, idx_rut-3), idx_rut+1):
                cand = search_range[j].strip()
                if len(cand) > 3 and not re.search(r"\b(FACTURA|BOLETA|NOTA|RUT|R\.U\.T|FOLIO|SII|ELECTR[ÓO]NICA)\b", cand, re.IGNORECASE):
                    return _pretty_name(cand)

    for cand in search_range[:15]:
        c = cand.strip()
        if len(c) >= 6 and (c.isupper() or " SPA" in c or " LTDA" in c or " S.A" in c):
            if not re.search(r"\b(FACTURA|BOLETA|NOTA|RUT|R\.U\.T|FOLIO|SII|ELECTR[ÓO]NICA)\b", c, re.IGNORECASE):
                return _pretty_name(c)
    return None

def _line_has_rut(line: str) -> bool:
    return bool(re.search(r"\bR\.?\s*U\.?\s*T\.?|RUT", line, re.IGNORECASE))

def _collect_amounts_near(lines: List[str], window_ahead: int = 8, window_back: int = 1) -> Dict[str, List[Decimal]]:
    out: Dict[str, List[Decimal]] = {}
    U = [ln.upper() for ln in lines]
    for key, pat in LABELS_MONTOS.items():
        out[key] = []
        regex = re.compile(pat, re.IGNORECASE)
        for idx, up in enumerate(U):
            if regex.search(up):
                for j in range(max(0, idx-window_back), min(idx+window_ahead+1, len(lines))):
                    if _line_has_rut(lines[j]): 
                        continue
                    out[key] += _montos_en_linea(lines[j])
    return out

def _parse_montos(text: str, tipo: str, iva_rate: Decimal) -> Dict[str, Optional[Decimal]]:
    campos: Dict[str, Optional[Decimal]] = {"monto_neto": None, "monto_exento": None, "iva": None, "total": None}
    lines = text.splitlines()

    # 1) Candidatos por cercanía a etiquetas (ventana amplia)
    nearby = _collect_amounts_near(lines, window_ahead=8, window_back=1)
    for key in ["monto_neto","monto_exento","iva","total"]:
        cands = [c for c in nearby.get(key, []) if c is not None]
        if cands:
            campos[key] = (cands[-1] if key == "total" else max(cands))

    # 2) Fallbacks: ignora líneas con RUT
    todos: List[Decimal] = []
    for ln in lines:
        if _line_has_rut(ln):
            continue
        todos += _montos_en_linea(ln)

    if campos["total"] is None and todos:
        campos["total"] = max(todos, key=lambda z: abs(z))

    # 3) Derivaciones
    if campos["total"] is not None and campos["iva"] is None:
        neto = campos["monto_neto"]
        exento = campos["monto_exento"] or Decimal("0")
        if neto is not None:
            posible_iva = campos["total"] - neto - exento
            if abs(posible_iva) < Decimal("2"):
                posible_iva = (neto * iva_rate / Decimal("100")).quantize(Decimal("1"))
            campos["iva"] = posible_iva if posible_iva != 0 else None

    if campos["monto_neto"] is None and campos["total"] is not None:
        exento = campos["monto_exento"] or Decimal("0")
        if campos["iva"] is not None:
            campos["monto_neto"] = campos["total"] - exento - campos["iva"]
        else:
            neto_est = (campos["total"] - exento) / (Decimal("1") + (iva_rate/Decimal("100")))
            campos["monto_neto"] = _round0(neto_est)
            iva_est = campos["total"] - exento - campos["monto_neto"]
            campos["iva"] = iva_est if abs(iva_est) > 0 else None

    if tipo.startswith("nota_credito"):
        for k in ["monto_neto","monto_exento","iva","total"]:
            v = campos[k]
            if v is not None and v > 0:
                campos[k] = -v

    for k in ["monto_neto","iva","total"]:
        v = campos[k]
        if v is not None:
            campos[k] = _round0(v)

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

# -----------------------------------------------------------------------------
# Extracción de texto
# -----------------------------------------------------------------------------
def _text_from_pdf(path: str) -> str:
    try:
        text = extract_text(path) or ""
        if len(text.strip()) > 40:
            return text
    except Exception as e:
        logger.warning(f"Fallo extract_text PDF: {e}")

    try:
        images = convert_from_path(path, fmt="png", dpi=300, poppler_path=_POPPLER_PATH)
        ocr_texts = []
        for im in images:
            im = ImageOps.exif_transpose(im).convert("L").filter(ImageFilter.MedianFilter(3))
            ocr_texts.append(
                pytesseract.image_to_string(
                    im, lang=DEFAULT_TESSERACT_LANG,
                    config=f"--psm {DEFAULT_TESSERACT_PSM} --oem {DEFAULT_TESSERACT_OEM}"
                )
            )
        return "\n".join(ocr_texts)
    except Exception as e:
        logger.error(f"Fallo OCR PDF: {e}")
        return ""

def _text_from_imagefile(path: str) -> str:
    try:
        im = Image.open(path)
        im = ImageOps.exif_transpose(im).convert("L").filter(ImageFilter.MedianFilter(3))
        return pytesseract.image_to_string(
            im, lang=DEFAULT_TESSERACT_LANG,
            config=f"--psm {DEFAULT_TESSERACT_PSM_IMAGE} --oem {DEFAULT_TESSERACT_OEM}",
        )
    except Exception as e:
        logger.error(f"Fallo OCR imagen: {e}")
        return ""

# -----------------------------------------------------------------------------
# API pública
# -----------------------------------------------------------------------------
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
    fuente_texto: str = "desconocido"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # serializables friendly (Decimales a str)
        for k in ["iva_tasa","monto_neto","monto_exento","iva","total"]:
            v = data.get(k)
            if isinstance(v, Decimal):
                data[k] = str(v)
        return data

def parse_text(text: str) -> OCRResult:
    raw = _preprocess_text(text or "")
    tipo = _guess_tipo(raw)
    iva_rate = _guess_iva_rate(raw) or Decimal("19")

    rut = _select_proveedor_rut(raw)
    if rut:
        rut = rut.replace(".", "").upper()

    m_f = FOLIO_RE.search(raw)
    folio = m_f.group(1) if m_f else None

    fecha = _extract_first_date(raw)
    proveedor_nombre = _extract_proveedor(raw.splitlines(), rut)
    montos = _parse_montos(raw, tipo, iva_rate)

    return OCRResult(
        raw_text=raw, rut_proveedor=rut or "", proveedor_nombre=proveedor_nombre or "",
        folio=folio or "", fecha_emision=fecha, tipo_documento=tipo, iva_tasa=iva_rate, **montos,
        fuente_texto="unknown",
    )

def parse_file(path: str, mime: Optional[str] = None) -> Dict[str, Any]:
    mime = mime or mimetypes.guess_type(path)[0] or ""
    if mime.startswith("application/pdf") or path.lower().endswith(".pdf"):
        text = _text_from_pdf(path)
        fuente = "pdf_text" if len(text.strip()) > 40 else "pdf_ocr"
    elif mime.startswith("image/"):
        text = _text_from_imagefile(path)
        fuente = "image_ocr"
    else:
        text = _text_from_pdf(path) if path.lower().endswith(".pdf") else ""
        fuente = "pdf_text" if len(text.strip()) > 40 else "unknown"

    result = parse_text(text)
    result.fuente_texto = fuente

    logger.info(
        f"OCR parse_file: tipo={result.tipo_documento}, rut={result.rut_proveedor}, "
        f"folio={result.folio}, fecha={result.fecha_emision}, total={result.total}"
    )
    return result.to_dict()
