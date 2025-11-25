import csv
import openpyxl
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Sum, IntegerField
from django.db.models.functions import Coalesce
from django.shortcuts import render
from apps.documentos.models import Documento, TIPOS
from apps.empresas.utils import get_empresa_activa
from apps.empresas.models import Empresa

class ReportsView(View):
    template_name = "panel/reportes.html"

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return self.get_report_data(request)
        return render(request, self.template_name)

def get_report_data(self, request):
    today = datetime.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    try:
        empresa_activa = get_empresa_activa(request)
    except Empresa.DoesNotExist:
        return JsonResponse({'error': 'No se ha seleccionado una empresa.'}, status=400)

    # --- CAMBIO 1: Filtrar por fecha de emisión real, no por fecha de subida ---
    # Esto asegura que si subes hoy una factura de hace 2 meses, aparezca en el reporte de hace 2 meses.
    docs = Documento.objects.filter(
        empresa=empresa_activa,
        fecha_emision__year=year,
        fecha_emision__month=month,
        fecha_emision__isnull=False  # Solo documentos que el OCR haya detectado fecha
    )
    
    # Cálculos de Ingresos (Facturas y Boletas)
    # Nota: Tu lista de tipos ya incluye Facturas y Boletas (Afectas y Exentas)
    ingresos = docs.filter(
        tipo_documento__in=['factura_afecta', 'factura_exenta', 'boleta_afecta', 'boleta_exenta']
    ).aggregate(
        total=Coalesce(Sum('total'), 0, output_field=IntegerField())
    )['total']

    # Cálculos de Gastos (Notas de Crédito y otros si agregas más tipos a futuro)
    gastos = docs.filter(tipo_documento__in=['nota_credito']).aggregate(
        total=Coalesce(Sum('total'), 0, output_field=IntegerField())
    )['total']

    kpis = {
        'total_ingresos': ingresos,
        'total_gastos': gastos,
        'resultado_mes': ingresos - gastos
    }

    # Datos para gráficos
    charts_data = {
        'ingresos_gastos': {'ingresos': ingresos, 'gastos': gastos},
        'analisis_iva': {
            'iva_credito': docs.filter(tipo_documento__in=['nota_credito']).aggregate(
                total=Coalesce(Sum('iva'), 0, output_field=IntegerField())
            )['total'],
            'iva_debito': docs.filter(tipo_documento__in=['factura_afecta', 'boleta_afecta']).aggregate(
                total=Coalesce(Sum('iva'), 0, output_field=IntegerField())
            )['total']
        },
        'distribucion_ingresos': {
            tipo[1]: docs.filter(tipo_documento=tipo[0], total__gt=0).count()
            for tipo in TIPOS if tipo[0] not in ['nota_credito', 'desconocido']
        },
        'distribucion_gastos': {
            'Notas de Crédito': docs.filter(tipo_documento='nota_credito').count()
        }
    }
    
    # --- CAMBIO 2: Ordenar por fecha de emisión y NO enmascarar el dato ---
    ultimos_documentos = list(docs.order_by('-fecha_emision')[:10].values(
        'folio', 'tipo_documento', 'fecha_emision', 'total'
    ))
    
    tipo_display_map = dict(TIPOS)
    for doc in ultimos_documentos:
        doc['monto_total'] = doc.pop('total')
        doc['tipo_documento_display'] = tipo_display_map.get(doc['tipo_documento'], 'Desconocido')
        
        # --- CAMBIO 3: Usar la fecha real de emisión ---
        # Eliminamos el código anterior que sobrescribía fecha_emision con creado_en
        fecha_real = doc.get('fecha_emision')
        if fecha_real and hasattr(fecha_real, 'strftime'):
            doc['fecha_emision'] = fecha_real.strftime('%Y-%m-%d')
        else:
            doc['fecha_emision'] = "Pendiente" # O 'N/A' si el OCR no la leyó

    response_data = {
        'kpis': kpis,
        'charts': charts_data,
        'ultimos_documentos': ultimos_documentos
    }
    return JsonResponse(response_data)


def export_report_data(request):
    today = datetime.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    file_type = request.GET.get('file_type', 'csv')
    
    try:
        empresa_activa = get_empresa_activa(request)
    except Empresa.DoesNotExist:
        return HttpResponse("No se ha seleccionado una empresa.", status=400)

    docs = Documento.objects.filter(
        empresa=empresa_activa,
        fecha_emision__isnull=False,
        fecha_emision__year=year,
        fecha_emision__month=month
    ).order_by('fecha_emision')

    filename = f"reporte_{empresa_activa.rut}_{year}_{month}"
    
    # --- Función auxiliar para formatear fechas de forma segura ---
    def format_date_safely(date_obj):
        if date_obj and hasattr(date_obj, 'strftime'):
            return date_obj.strftime('%Y-%m-%d')
        return "" # Retorna un string vacío si la fecha es nula

    if file_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        response.write(u'\ufeff'.encode('utf8'))
        
        writer = csv.writer(response)
        writer.writerow(['Folio', 'Tipo de Documento', 'Fecha de Emisión', 'RUT Proveedor', 'Monto Neto', 'Monto IVA', 'Monto Total'])
        
        for doc in docs:
            writer.writerow([
                doc.folio,
                doc.get_tipo_documento_display(),
                format_date_safely(doc.fecha_emision), # <-- CORREGIDO
                doc.rut_proveedor,
                doc.monto_neto,
                doc.iva,
                doc.total,
            ])
        return response

    elif file_type == 'excel':
        # ... (el resto del código de exportación a Excel permanece igual)
        pass
    
    return HttpResponse("Tipo de archivo no válido.", status=400)

class ValidationsView(TemplateView):
    template_name = "panel/validaciones.html"