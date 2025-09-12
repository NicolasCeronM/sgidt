# apps/panel/views/dashboard.py
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.panel.utils.empresa import get_empresa_activa
from apps.panel.queries.documentos import (
    rango_mes_actual, qs_base_por_empresa,
    docs_mes_por_carga, docs_mes_por_emision,
    kpis_desde_qs
)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "panel/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        empresa = get_empresa_activa(self.request)
        inicio, fin = rango_mes_actual()

        qs_base = qs_base_por_empresa(empresa)

        # Variante A: actividad del mes (subidos/creado_en)
        qs_subidos = docs_mes_por_carga(qs_base, inicio, fin)
        kpis_subidos = kpis_desde_qs(qs_subidos)

        # Variante B: emitidos este mes (fecha_emision) - usable si luego pones un toggle
        qs_emitidos = docs_mes_por_emision(qs_base, inicio, fin)
        kpis_emitidos = kpis_desde_qs(qs_emitidos)

        ctx.update({
            "empresa": empresa,

            # KPIs usados por el template actual (actividad del mes)
            "kpi_docs_mes":  kpis_subidos["docs"],
            "kpi_iva_mes":   kpis_subidos["iva"],
            "kpi_gasto_mes": kpis_subidos["gasto"],

            # Extras opcionales para UI futura (por emisión)
            "kpi_docs_mes_emitidos":  kpis_emitidos["docs"],
            "kpi_iva_mes_emitidos":   kpis_emitidos["iva"],
            "kpi_gasto_mes_emitidos": kpis_emitidos["gasto"],

            # Timeline: últimos 5 según fecha de carga (actividad visible del mes)
            "ultimos_docs": qs_subidos.order_by("-creado_en")[:5],
        })
        return ctx
