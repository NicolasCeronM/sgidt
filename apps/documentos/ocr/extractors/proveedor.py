# apps/documentos/ocr/extractors/proveedor.py
import re
from ..utils.rut import is_valid, clean_rut, format_rut

RUT_PATTERNS = [
    re.compile(r'(?:R\.?U\.?T\.?|RUT|ROL)[\s:.]*(\d{1,2}\.\d{3}\.\d{3}-[\dkK])'),
    re.compile(r'(\d{1,2}\.\d{3}\.\d{3}-[\dkK])')
]
RECEPTOR_KEYWORDS = re.compile(r'SEÑOR\(ES\)|RECEPTOR|CLIENTE', re.I)
COMPANY_KEYWORDS = re.compile(r'\b(SpA|Spa|LTDA|Ltda|EIRL|S\.A\.)\b', re.I)

def extract_emisor_receptor(texto_general: str) -> tuple[dict, dict]:
    emisor, receptor = {}, {}
    lines = texto_general.split('\n')
    
    # Dividir el texto en antes y después de la sección del cliente
    receptor_section_start = -1
    for i, line in enumerate(lines):
        if RECEPTOR_KEYWORDS.search(line):
            receptor_section_start = i
            break
            
    emisor_text = "\n".join(lines[:receptor_section_start]) if receptor_section_start != -1 else texto_general
    receptor_text = "\n".join(lines[receptor_section_start:]) if receptor_section_start != -1 else ""

    # --- Búsqueda del Emisor (Proveedor) ---
    emisor_ruts = [format_rut(m.group(1)) for p in RUT_PATTERNS for m in p.finditer(emisor_text) if is_valid(m.group(1))]
    if emisor_ruts:
        emisor['rut'] = emisor_ruts[0]

    # Estrategia de nombre del emisor: buscar en las primeras líneas
    for line in emisor_text.split('\n')[:6]:
        line = line.strip()
        # Un buen nombre no es un RUT, ni un giro, ni una dirección
        if len(line) > 5 and not is_valid(line) and "GIRO" not in line.upper() and "DIRECCION" not in line.upper():
             # Si es un nombre de empresa o parece un nombre de persona (mayúsculas)
             if COMPANY_KEYWORDS.search(line) or (line.isupper() and len(line.split()) > 1):
                emisor['razon_social'] = line
                break
    
    # --- Búsqueda del Receptor (Cliente) ---
    if receptor_text:
        receptor_ruts = [format_rut(m.group(1)) for p in RUT_PATTERNS for m in p.finditer(receptor_text) if is_valid(m.group(1))]
        if receptor_ruts:
            receptor['rut'] = receptor_ruts[0]
            
    # Si no se encontró el RUT del emisor, tomar el que no es del receptor
    if not emisor.get('rut'):
        all_ruts = {format_rut(m.group(1)) for p in RUT_PATTERNS for m in p.finditer(texto_general) if is_valid(m.group(1))}
        receptor_rut_set = {receptor.get('rut')}
        possible_emisor_ruts = all_ruts - receptor_rut_set
        if possible_emisor_ruts:
            emisor['rut'] = possible_emisor_ruts.pop()
            
    return emisor, receptor