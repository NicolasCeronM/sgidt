# apps/panel/queries/documentos.py
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import Coalesce
from apps.documentos.models import Documento

def rango_mes_actual():
    hoy = timezone.localdate()
    return hoy.replace(day=1), hoy

def qs_base_por_empresa(empresa):
    qs = Documento.objects.all()
    return qs.filter(empresa=empresa) if empresa else qs.none()

def docs_mes_por_carga(qs, inicio, fin):
    """Documentos cargados este mes (creado_en)."""
    return qs.filter(creado_en__date__gte=inicio, creado_en__date__lte=fin)

def docs_mes_por_emision(qs, inicio, fin):
    """Documentos emitidos este mes (fecha_emision)."""
    return qs.filter(fecha_emision__isnull=False, fecha_emision__gte=inicio, fecha_emision__lte=fin)

def kpis_desde_qs(qs):
    """Retorna totales robustos (NULL-safe)."""
    return {
        "docs": qs.count(),
        "iva": qs.aggregate(v=Coalesce(Sum("iva"),   Decimal(0)))["v"] or Decimal(0),
        "gasto": qs.aggregate(v=Coalesce(Sum("total"), Decimal(0)))["v"] or Decimal(0),
    }
