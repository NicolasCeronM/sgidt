# apps/panel/views/api.py
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.panel.utils.empresa import get_empresa_activa
from apps.panel.queries.documentos import (
    rango_mes_actual, qs_base_por_empresa,
    docs_mes_por_carga, docs_mes_por_emision,
    kpis_desde_qs
)
from apps.panel.serializers import DocumentoMiniSerializer

# IMPORTANTE: Importamos el servicio de alertas compartido
from apps.documentos.services.alerts import get_empresa_alerts


class DashboardSummaryApi(APIView):
    """
    Resumen de KPIs del dashboard.
    GET -> /panel/api/dashboard/summary/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        empresa = get_empresa_activa(request)
        inicio, fin = rango_mes_actual()
        qs_base = qs_base_por_empresa(empresa)

        # 1. Actividad del mes (KPIs financieros)
        qs_subidos = docs_mes_por_carga(qs_base, inicio, fin)
        kpis_subidos = kpis_desde_qs(qs_subidos)

        # (Opcional) Por emisión
        qs_emitidos = docs_mes_por_emision(qs_base, inicio, fin)
        kpis_emitidos = kpis_desde_qs(qs_emitidos)

        # 2. CALCULAR ALERTAS (Usando la misma lógica del sidebar y correo)
        # Esto asegura que si el sidebar dice "3", el dashboard también diga "3"
        alertas_data = get_empresa_alerts(empresa)
        
        # Definimos "Prioritarias" como documentos con ERROR o pendientes de SII
        # (Las facturas vencidas pueden ser menos críticas para este contador rápido)
        total_prioritarias = alertas_data['sii_pending'].count() + alertas_data['errores'].count()

        def _num(x):
            # Helper para devolver números JSON-safe
            if x is None:
                return 0
            if isinstance(x, Decimal):
                return float(x)
            return x

        data = {
            "empresa": {
                "id": empresa.id,
                "nombre": empresa.nombre,
                "rut": empresa.rut,
            },
            "mes": {
                "inicio": inicio.isoformat(),
                "fin": fin.isoformat(),
            },
            "kpis_carga": {
                "docs": _num(kpis_subidos["docs"]),
                "iva": _num(kpis_subidos["iva"]),
                "gasto": _num(kpis_subidos["gasto"]),
                # Si el frontend espera deltas, los enviamos en 0 por ahora
                "delta_docs": 0,
                "delta_iva": 0,
                "delta_gasto": 0,
            },
            "kpis_emision": {
                "docs": _num(kpis_emitidos["docs"]),
                "iva": _num(kpis_emitidos["iva"]),
                "gasto": _num(kpis_emitidos["gasto"]),
            },
            # SECCIÓN DE ALERTAS PARA EL DASHBOARD.JS
            "alertas": {
                "total": alertas_data['total'],          # Total global (Vencidos + Errores + SII)
                "prioritarias": total_prioritarias       # Solo Errores + SII Pendiente
            }
        }
        return Response(data)


class DashboardLatestDocsApi(APIView):
    """
    Últimos documentos del mes por fecha de carga (timeline)
    GET -> /panel/api/dashboard/latest/?limit=5
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        empresa = get_empresa_activa(request)
        inicio, fin = rango_mes_actual()
        qs_base = qs_base_por_empresa(empresa)
        qs_subidos = docs_mes_por_carga(qs_base, inicio, fin)

        try:
            limit = int(request.query_params.get("limit", 5))
        except Exception:
            limit = 5
        
        # Ordenamos por fecha de creación descendente
        qs = qs_subidos.order_by("-creado_en")[:max(1, min(limit, 50))]

        serializer = DocumentoMiniSerializer(qs, many=True)
        return Response({
            "count": qs.count(),
            "results": serializer.data
        })