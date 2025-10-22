# -*- coding: utf-8 -*-
from dataclasses import dataclass, asdict
from datetime import date
from decimal import Decimal
from typing import Optional, Any, Dict

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
        for k in ("iva_tasa", "monto_neto", "monto_exento", "iva", "total"):
            v = data.get(k)
            if isinstance(v, Decimal):
                data[k] = str(v)
        return data
