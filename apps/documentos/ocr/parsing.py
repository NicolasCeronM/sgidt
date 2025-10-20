# apps/documentos/ocr/parsing.py

from pathlib import Path
from pprint import pprint # Usaremos pprint para que se vea más ordenado
from .schema import OCRResult
# --- Usando los nombres correctos de TUS archivos ---
from .engines.pdf import read_pdf_text
from .engines.image import ocr_from_image_path
# ---------------------------------------------------
from .utils.text_norm import preprocess_text
from .detectors.tipo_doc import detect_tipo_dte
from .extractors.folio_fecha import extract_folio, extract_fecha
from .extractors.proveedor import extract_emisor_receptor
from .extractors.amounts import extract_amounts
from .postprocess.reconcile import reconcile_amounts

def get_text_from_file(path: str) -> tuple[str, str]:
    """
    Lee el texto de un PDF o una imagen y devuelve el texto y la fuente.
    """
    fpath = Path(path)
    raw_text = ""

    if fpath.suffix.lower() == ".pdf":
        raw_text = read_pdf_text(path)
        return raw_text or "", "pdf_text"
    else:
        raw_text = ocr_from_image_path(path)
        return raw_text or "", "image_ocr"


def parse_text(raw_text: str) -> OCRResult:
    """
    Procesa el texto plano extraído para obtener los datos estructurados.
    """
    print("\n" + "="*50)
    print("INICIANDO MODO DE DIAGNÓSTICO OCR")
    print("="*50)
    
    # Imprime una parte del texto crudo para verificar que se leyó bien
    print("\n--- 1. TEXTO CRUDO EXTRAÍDO DEL DOCUMENTO ---")
    # Usamos repr() para ver caracteres invisibles como saltos de línea (\n)
    print(repr(raw_text or ""))
    print("-"*(50))

    text = preprocess_text(raw_text or "")
    
    print("\n--- 2. EXTRACCIONES INDIVIDUALES ---")
    tipo_doc_tuple = detect_tipo_dte(text)
    tipo_doc = tipo_doc_tuple[0] if isinstance(tipo_doc_tuple, tuple) else tipo_doc_tuple
    print(f"Tipo DTE detectado: {tipo_doc}")

    folio, _ = extract_folio(text)
    print(f"Folio extraído: {folio}")

    fecha, _ = extract_fecha(text)
    print(f"Fecha extraída: {fecha}")
    
    emisor, _ = extract_emisor_receptor(text)
    rut_proveedor = emisor.get('rut', '')
    nombre_proveedor = emisor.get('razon_social', '')
    print(f"Proveedor extraído: RUT='{rut_proveedor}', Nombre='{nombre_proveedor}'")
    print("-"*(50))

    # --- ¡EL PUNTO MÁS IMPORTANTE! ---
    print("\n--- 3. EXTRACCIÓN DE MONTOS (ANTES DE CORREGIR) ---")
    extracted_montos = extract_amounts(text)
    pprint(extracted_montos)
    print("-"*(50))
    
    print("\n--- 4. RECONCILIACIÓN DE MONTOS (DESPUÉS DE CORREGIR) ---")
    reconciled_montos = reconcile_amounts(extracted_montos)
    pprint(reconciled_montos)
    print("-"*(50))

    final_result = OCRResult(
        raw_text=raw_text,
        rut_proveedor=rut_proveedor,
        proveedor_nombre=nombre_proveedor,
        folio=str(folio) if folio else "",
        fecha_emision=fecha,
        tipo_documento=tipo_doc,
        **reconciled_montos
    )

    print("\n--- 5. RESULTADO FINAL ANTES DE GUARDAR EN BD ---")
    pprint(vars(final_result)) # Usamos vars() para ver el contenido del objeto
    print("="*50)
    print("FIN DE DIAGNÓSTICO")
    print("="*50 + "\n")
    
    return final_result

def parse_document(path: str) -> tuple[OCRResult, str]:
    """
    Orquestador principal: recibe la ruta de un archivo, extrae el texto y lo parsea.
    """
    raw_text, source = get_text_from_file(path)
    result = parse_text(raw_text)
    result.fuente_texto = source
    
    return result, raw_text