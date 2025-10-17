import re

# --- INICIO: Funciones de utilidad integradas ---

def clean_rut(rut: str) -> str:
    if not isinstance(rut, str): return ""
    return rut.replace(".", "").replace("-", "").upper()

def validate_rut(rut: str) -> bool:
    rut = clean_rut(rut)
    if not rut or not rut[:-1].isdigit() or len(rut) < 2: return False
    cuerpo, dv = rut[:-1], rut[-1]
    try:
        suma = sum(int(d) * (2 + i % 6) for i, d in enumerate(reversed(cuerpo)))
        dv_calculado = str(11 - (suma % 11))
        if dv_calculado == '11': dv_esperado = '0'
        elif dv_calculado == '10': dv_esperado = 'K'
        else: dv_esperado = dv_calculado
        return dv == dv_esperado
    except (ValueError, TypeError): return False

def format_rut(rut: str) -> str:
    rut = clean_rut(rut)
    if not rut: return ""
    cuerpo, dv = rut[:-1], rut[-1]
    cuerpo_formateado = f"{int(cuerpo):,}".replace(",", ".")
    return f"{cuerpo_formateado}-{dv}"

def normalize_text(text: str) -> str:
    if not isinstance(text, str): return ""
    return ' '.join(text.split()).strip()

# --- FIN: Funciones de utilidad integradas ---

RUT_PATTERNS = [
    re.compile(r'(?:R\.?U\.?T\.?|RUT|ROL)[\s:.]*(\d{1,2}\.\d{3}\.\d{3}-[\dkK])'),
    re.compile(r'(\d{1,2}\.\d{3}\.\d{3}-[\dkK])')
]

def extract_emisor_receptor(texto_general: str) -> tuple[dict, dict]:
    emisor, receptor = {}, {}
    if not texto_general:
        return emisor, receptor

    rut_matches = []
    for pattern in RUT_PATTERNS:
        for match in pattern.finditer(texto_general):
            rut_str = match.group(1)
            if validate_rut(clean_rut(rut_str)):
                rut_matches.append(format_rut(rut_str))
    
    unique_ruts = list(dict.fromkeys(rut_matches))
    if len(unique_ruts) > 0: emisor['rut'] = unique_ruts[0]
    if len(unique_ruts) > 1: receptor['rut'] = unique_ruts[1]

    razon_social_pattern = re.compile(r'([A-Z\s.,]+(?:S\.A\.|LTDA\.|E\.I\.R\.L\.|SpA))', re.IGNORECASE)
    rs_match = razon_social_pattern.search(texto_general)
    if rs_match:
        emisor['nombre'] = normalize_text(rs_match.group(1).strip())
        
    return emisor, receptor