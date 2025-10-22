# apps/panel/views/dashboard.py

from datetime import date, datetime
from calendar import month_abbr

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.views.generic import TemplateView

from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.panel.utils.empresa import get_empresa_activa
from apps.panel.queries.documentos import (
    rango_mes_actual, qs_base_por_empresa,
    docs_mes_por_carga, docs_mes_por_emision, kpis_desde_qs
)


# ============ VISTA DEL DASHBOARD ============
class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Renderiza el dashboard principal.
    Calcula KPIs básicos: documentos, IVA y gasto del mes.
    """
    template_name = "panel/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Empresa activa del usuario
        empresa = get_empresa_activa(self.request)

        # Rango de fechas del mes actual
        inicio, fin = rango_mes_actual()

        # Query base por empresa
        qs_base = qs_base_por_empresa(empresa)

        # KPIs por fecha de carga (subidos este mes)
        qs_subidos = docs_mes_por_carga(qs_base, inicio, fin)
        kpis_subidos = kpis_desde_qs(qs_subidos)

        # KPIs por fecha de emisión (opcional, si luego quieres un toggle en el UI)
        qs_emitidos = docs_mes_por_emision(qs_base, inicio, fin)
        kpis_emitidos = kpis_desde_qs(qs_emitidos)

        # Inyecta en contexto los KPIs
        ctx.update({
            "empresa": empresa,
            "kpi_docs_mes":  kpis_subidos["docs"],
            "kpi_iva_mes":   kpis_subidos["iva"],
            "kpi_gasto_mes": kpis_subidos["gasto"],

            # Extras para futura UI (comparación por emisión)
            "kpi_docs_mes_emitidos":  kpis_emitidos["docs"],
            "kpi_iva_mes_emitidos":   kpis_emitidos["iva"],
            "kpi_gasto_mes_emitidos": kpis_emitidos["gasto"],
        })
        return ctx


# ============ API: GASTOS ÚLTIMOS 6 MESES ============
class GastosUltimos6MesesAPI(LoginRequiredMixin, APIView):
    """
    Devuelve un arreglo de los últimos 6 meses con el gasto total:
    [
      {"label": "Ago", "total": 123456},
      {"label": "Sep", "total": 987654},
      ...
    ]
    Usa el campo de fecha disponible (creado_en o fecha_emision).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        empresa = get_empresa_activa(request)
        qs = qs_base_por_empresa(empresa)

        # Detecta campo de fecha disponible en el modelo
        model = qs.model

        def has_field(name: str) -> bool:
            try:
                model._meta.get_field(name)
                return True
            except Exception:
                return False

        date_field = "creado_en" if has_field("creado_en") else (
            "fecha_emision" if has_field("fecha_emision") else None
        )
        if not date_field:
            return JsonResponse(
                {"detail": "No se encontró un campo de fecha (creado_en/fecha_emision) en Documento."},
                status=500
            )

        today = date.today()
        series = []

        # Recorremos los últimos 6 meses (incluye mes actual)
        for i in range(5, -1, -1):
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1

            # Inicio y fin del mes
            start = make_aware(datetime(year, month, 1, 0, 0, 0))
            end = make_aware(datetime(
                year + (1 if month == 12 else 0),
                1 if month == 12 else month + 1,
                1, 0, 0, 0
            ))

            # Filtro dinámico según campo detectado
            filtro = {f"{date_field}__gte": start, f"{date_field}__lt": end}
            month_qs = qs.filter(**filtro)

            # Suma segura del campo "total" (ajusta si tu campo se llama distinto)
            total = month_qs.aggregate(
                s=Coalesce(
                    Sum("total", output_field=DecimalField(max_digits=18, decimal_places=2)),
                    Value(0, output_field=DecimalField(max_digits=18, decimal_places=2))
                )
            )["s"]

            # Agregamos resultado a la serie
            series.append({
                "label": month_abbr[month],   # Ej: 'Aug', 'Sep'. Cambia si prefieres 'Ago'
                "total": int(total or 0),     # Entero CLP para ApexCharts
            })

        return JsonResponse(series, safe=False)
