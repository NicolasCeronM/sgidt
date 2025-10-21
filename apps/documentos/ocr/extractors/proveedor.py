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
    
    # 1. Dividir el documento en sección de emisor y receptor
    receptor_section_start = -1
    for i, line in enumerate(lines):
        if RECEPTOR_KEYWORDS.search(line):
            receptor_section_start = i
            break
            
    emisor_text = "\n".join(lines[:receptor_section_start]) if receptor_section_start != -1 else texto_general
    receptor_text = "\n".join(lines[receptor_section_start:]) if receptor_section_start != -1 else ""

    # 2. Buscar el RUT y nombre del EMISOR solo en su sección
    emisor_ruts = [format_rut(m.group(1)) for p in RUT_PATTERNS for m in p.finditer(emisor_text) if is_valid(m.group(1))]
    if emisor_ruts:
        emisor['rut'] = emisor_ruts[0]

    for line in emisor_text.split('\n')[:7]: # Buscar en las primeras 7 líneas de la sección del emisor
        line = line.strip()
        if len(line) > 5 and not is_valid(line) and "GIRO" not in line.upper() and "DIRECCION" not in line.upper():
             if COMPANY_KEYWORDS.search(line) or (line.isupper() and len(line.split()) > 1 and not any(char.isdigit() for char in line)):
                emisor['razon_social'] = line
                break
    
    # 3. Buscar el RUT del RECEPTOR solo en su sección
    if receptor_text:
        receptor_ruts = [format_rut(m.group(1)) for p in RUT_PATTERNS for m in p.finditer(receptor_text) if is_valid(m.group(1))]
        if receptor_ruts:
            receptor['rut'] = receptor_ruts[0]
            
    # 4. Fallback por si la división falló o el RUT estaba en un lugar inesperado
    if not emisor.get('rut'):
        all_ruts_on_doc = {format_rut(m.group(1)) for p in RUT_PATTERNS for m in p.finditer(texto_general) if is_valid(m.group(1))}
        receptor_rut_set = {receptor.get('rut')}
        possible_emisor_ruts = all_ruts_on_doc - receptor_rut_set
        if possible_emisor_ruts:
            emisor['rut'] = possible_emisor_ruts.pop()
            
    return emisor, receptor