# apps/documentos/api/v1/filters.py
from django.utils.dateparse import parse_date
from datetime import date, datetime

def apply_document_filters(request, qs):
    f_desde = request.query_params.get("from") or request.query_params.get("date_from") or request.query_params.get("dateFrom")
    f_hasta = request.query_params.get("to") or request.query_params.get("date_to") or request.query_params.get("dateTo")
    tipo  = request.query_params.get("type") or request.query_params.get("docType")
    estado= request.query_params.get("status") or request.query_params.get("docStatus")

    if f_desde:
        fd = parse_date(f_desde)
        if isinstance(fd, datetime): fd = fd.date()
        if isinstance(fd, date): qs = qs.filter(fecha_emision__gte=fd)
    if f_hasta:
        fh = parse_date(f_hasta)
        if isinstance(fh, datetime): fh = fh.date()
        if isinstance(fh, date): qs = qs.filter(fecha_emision__lte=fh)

    if tipo:
        t = tipo.lower()
        if t == "factura": qs = qs.filter(tipo_documento__startswith="factura_")
        elif t == "boleta": qs = qs.filter(tipo_documento__startswith="boleta_")
        elif t in {"nc","nota_credito"}: qs = qs.filter(tipo_documento="nota_credito")

    if estado:
        e = estado.lower()
        if e in {"cola","pendiente"}: qs = qs.filter(estado__in=["pendiente","procesando"])
        elif e in {"procesado","validado"}: qs = qs.filter(estado="procesado")
        elif e == "error": qs = qs.filter(estado="error")

    return qs
