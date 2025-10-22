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
    Acepta 'month' y 'year' como query parameters.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            empresa_activa = get_empresa_activa(request)
        except Empresa.DoesNotExist:
            return Response({'error': 'No se ha seleccionado una empresa.'}, status=400)

        today = datetime.today()
        year = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))

        docs = Documento.objects.filter(
            empresa=empresa_activa,
            creado_en__year=year,
            creado_en__month=month
        )

        ingresos = docs.filter(tipo_documento__in=['factura_afecta', 'factura_exenta', 'boleta_afecta', 'boleta_exenta']).aggregate(
            total=Coalesce(Sum('total'), 0, output_field=IntegerField())
        )['total']
        gastos = docs.filter(tipo_documento__in=['nota_credito']).aggregate(
            total=Coalesce(Sum('total'), 0, output_field=IntegerField())
        )['total']

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
                'iva_credito': docs.filter(tipo_documento__in=['nota_credito']).aggregate(
                    total=Coalesce(Sum('iva'), 0, output_field=IntegerField())
                )['total'],
                'iva_debito': docs.filter(tipo_documento__in=['factura_afecta', 'boleta_afecta']).aggregate(
                    total=Coalesce(Sum('iva'), 0, output_field=IntegerField())
                )['total']
            },
            'distribucion_ingresos_chart': {
                tipo[1]: docs.filter(tipo_documento=tipo[0], total__gt=0).count()
                for tipo in TIPOS if tipo[0] not in ['nota_credito', 'desconocido']
            },
            'distribucion_gastos_chart': {
                'Notas de Crédito': docs.filter(tipo_documento='nota_credito').count()
            }
        }
        
        # --- CORREGIDO: Usamos 'instance' para serializar el objeto que creamos ---
        serializer = ReporteGeneralSerializer(instance=data)
        # No es necesario llamar a is_valid() cuando estamos serializando.
        
        return Response(serializer.data)
        # -------------------------------------------------------------------------