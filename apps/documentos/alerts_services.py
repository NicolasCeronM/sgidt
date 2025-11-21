from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from apps.documentos.models import Documento
from apps.empresas.models import Empresa

def check_and_notify_alerts():
    """
    Recorre todas las empresas activas y busca documentos con problemas
    para enviar un resumen por correo.
    """
    empresas = Empresa.objects.all() # Puedes filtrar por activas si tienes ese campo

    for empresa in empresas:
        alerts_data = get_empresa_alerts(empresa)
        
        # Si hay alertas, enviamos el correo
        if alerts_data['total_alerts'] > 0:
            send_alert_email(empresa, alerts_data)

def get_empresa_alerts(empresa):
    """
    Analiza los documentos de la empresa y retorna contadores y listas.
    """
    now = timezone.now().date()
    # Umbral para considerar "Vencido" (ej: 30 días después de emisión)
    limite_vencimiento = now - timedelta(days=30)

    # 1. Documentos pendientes de validación SII (llevan más de 24hrs procesados pero sin check SII)
    docs_sii_pending = Documento.objects.filter(
        empresa=empresa,
        estado='procesado',
        validado_sii=False,
        creado_en__lt=timezone.now() - timedelta(days=1) # Dar margen de 1 día
    )

    # 2. Documentos Vencidos (sin fecha de vencimiento en modelo, asumimos 30 días desde emisión)
    # Y que no estén "pagados" (si tuvieras ese estado) o simplemente informativos.
    docs_vencidos = Documento.objects.filter(
        empresa=empresa,
        fecha_emision__lt=limite_vencimiento,
        # Aquí podrías filtrar si ya están 'pagados' si tuvieras ese campo
    ).exclude(estado='error')

    # 3. Documentos con Error en OCR o Proceso
    docs_error = Documento.objects.filter(
        empresa=empresa,
        estado='error'
    )

    return {
        'sii_pending': docs_sii_pending,
        'vencidos': docs_vencidos,
        'errores': docs_error,
        'total_alerts': docs_sii_pending.count() + docs_vencidos.count() + docs_error.count()
    }

def send_alert_email(empresa, alerts_data):
    """
    Renderiza el template y envía el correo.
    """
    # Asumimos que quieres notificar al email configurado en la empresa
    # O puedes iterar sobre empresa.usuarios.all() si tienes esa relación
    destinatarios = []
    if empresa.email_host: # Usando un campo de ejemplo, ajusta a tu modelo real de contacto
         # Si tienes un campo 'email_contacto' o users relacionados:
         # destinatarios = [u.email for u in empresa.usuarios.all()]
         # Por ahora usaremos un placeholder o el mismo email de la empresa si sirve de contacto
         pass 
    
    # NOTA: Debes definir a quién le llega. 
    # Ejemplo: destinatarios = ['admin@empresa.com'] 
    
    if not destinatarios:
        return

    subject = f"⚠️ Alertas Pendientes - {empresa.rut}"
    
    context = {
        'empresa': empresa,
        'sii_pending': alerts_data['sii_pending'],
        'vencidos': alerts_data['vencidos'],
        'errores': alerts_data['errores'],
        'total': alerts_data['total_alerts'],
    }

    html_message = render_to_string('documentos/email/alerta_diaria.html', context)

    send_mail(
        subject,
        message="", # Versión texto plano (opcional)
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=destinatarios,
        html_message=html_message,
        fail_silently=True
    )