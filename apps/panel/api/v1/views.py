from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, IntegerField
from django.db.models.functions import Coalesce

from apps.documentos.models import Documento, TIPOS
from apps.empresas.utils import get_empresa_activa
from apps.empresas.models import Empresa
from .serializers import ReporteGeneralSerializer


class ReporteKpiAPIView(APIView):
    """
    API view para obtener los KPIs y datos de gráficos para los reportes.
    Acepta 'mes' y 'anio' desde el frontend, o 'month' y 'year'.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            empresa_activa = get_empresa_activa(request)
        except Empresa.DoesNotExist:
            return Response({'error': 'No se ha seleccionado una empresa.'}, status=400)

        today = datetime.today()

        # -----------------------------------------------
        #   ✔ CORREGIDO: aceptar mes/anio y month/year
        # -----------------------------------------------
        year = int(
            request.query_params.get('anio')
            or request.query_params.get('year')
            or today.year
        )

        month = int(
            request.query_params.get('mes')
            or request.query_params.get('month')
            or today.month
        )

        # -----------------------------------------------
        #   ✔ CORREGIDO: filtrar por FECHA DE EMISIÓN
        # -----------------------------------------------
        docs = Documento.objects.filter(
            empresa=empresa_activa,
            fecha_emision__year=year,
            fecha_emision__month=month
        )

        # -----------------------------------------------
        #   KPIs
        # -----------------------------------------------
        ingresos = docs.filter(
            tipo_documento__in=[
                'factura_afecta', 'factura_exenta',
                'boleta_afecta', 'boleta_exenta'
            ]
        ).aggregate(
            total=Coalesce(Sum('total'), 0, output_field=IntegerField())
        )['total']

        gastos = docs.filter(
            tipo_documento='nota_credito'
        ).aggregate(
            total=Coalesce(Sum('total'), 0, output_field=IntegerField())
        )['total']

        # -----------------------------------------------
        #   IVAs
        # -----------------------------------------------
        iva_credito = docs.filter(
            tipo_documento='nota_credito'
        ).aggregate(
            total=Coalesce(Sum('iva'), 0, output_field=IntegerField())
        )['total']

        iva_debito = docs.filter(
            tipo_documento__in=['factura_afecta', 'boleta_afecta']
        ).aggregate(
            total=Coalesce(Sum('iva'), 0, output_field=IntegerField())
        )['total']

        # -----------------------------------------------
        #   Distribuciones
        # -----------------------------------------------
        distrib_ing = {
            tipo[1]: docs.filter(tipo_documento=tipo[0], total__gt=0).count()
            for tipo in TIPOS
            if tipo[0] not in ['nota_credito', 'desconocido']
        }

        distrib_gas = {
            'Notas de Crédito': docs.filter(tipo_documento='nota_credito').count()
        }

        # -----------------------------------------------
        #   Ensamblar respuesta para el serializer
        # -----------------------------------------------
        data = {
            'kpis': {
                'total_ingresos': ingresos,
                'total_gastos': gastos,
                'resultado_mes': ingresos - gastos
            },
            'ingresos_vs_gastos_chart': {
                'ingresos': ingresos,
                'gastos': gastos
            },
            'analisis_iva_chart': {
                'iva_credito': iva_credito,
                'iva_debito': iva_debito
            },
            'distribucion_ingresos_chart': distrib_ing,
            'distribucion_gastos_chart': distrib_gas,
        }

        serializer = ReporteGeneralSerializer(instance=data)
        return Response(serializer.data)
