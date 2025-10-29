# apps/documentos/ocr/engines/xml.py

from lxml import etree
import logging
from decimal import Decimal

log = logging.getLogger(__name__)

def extract_data_from_xml(file_path):
    """
    Parsea un XML de DTE y extrae los datos principales en un formato
    consistente con el resultado del OCR.
    """
    try:
        tree = etree.parse(file_path)
        
        # El namespace es crucial para encontrar los elementos en XML del SII
        ns = {'sii': 'http://www.sii.cl/SiiDte'}

        # Mapeo de TipoDTE a nuestro tipo_documento
        tipo_dte_map = {
            '33': 'factura_afecta',
            '34': 'factura_exenta',
            '61': 'nota_credito',
            # Añade más mapeos según necesites
        }
        tipo_dte_code = tree.findtext('.//sii:TipoDTE', namespaces=ns)
        
        data = {
            "tipo_documento": tipo_dte_map.get(tipo_dte_code, 'desconocido'),
            "folio": tree.findtext('.//sii:Folio', namespaces=ns),
            "fecha_emision": tree.findtext('.//sii:FchEmis', namespaces=ns),
            "rut_proveedor": tree.findtext('.//sii:RUTEmisor', namespaces=ns),
            "proveedor_nombre": tree.findtext('.//sii:RznSoc', namespaces=ns),
            "monto_neto": Decimal(tree.findtext('.//sii:MntNeto', default='0', namespaces=ns)),
            "monto_exento": Decimal(tree.findtext('.//sii:MntExento', default='0', namespaces=ns)),
            "iva": Decimal(tree.findtext('.//sii:IVA', default='0', namespaces=ns)),
            "total": Decimal(tree.findtext('.//sii:MntTotal', default='0', namespaces=ns)),
            "iva_tasa": None, # El XML no siempre tiene la tasa explícita, se puede calcular
            "fuente_texto": "xml",
            "raw_text": etree.tostring(tree, pretty_print=True).decode('utf-8'),
        }

        # Calcular tasa de IVA si es posible
        if data["monto_neto"] and data["iva"]:
            try:
                tasa = (data["iva"] / data["monto_neto"]) * 100
                data["iva_tasa"] = Decimal(f"{tasa:.2f}")
            except Exception:
                pass # No se pudo calcular

        return data

    except Exception as e:
        log.error("Error crítico al parsear el archivo XML %s: %s", file_path, e)
        return None