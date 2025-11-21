# apps/documentos/services/alerts.py
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from apps.documentos.models import Documento
from apps.empresas.models import Empresa
import logging

logger = logging.getLogger(__name__)

def check_and_send_alerts():
    """
    Revisión diaria de documentos para todas las empresas.
    Envía un correo si detecta:
    1. Documentos procesados SIN validación SII por > 24h.
    2. Documentos con fecha de emisión > 30 días (Vencidos).
    3. Documentos en estado de ERROR.
    """
    logger.info("Iniciando servicio de alertas de documentos...")
    
    # Obtenemos empresas que tengan configurado algún correo (host/user) 
    # o simplemente todas si manejas el envío desde un correo central del sistema.
    empresas = Empresa.objects.all()

    for empresa in empresas:
        # Calculamos las alertas para esta empresa
        alertas = get_empresa_alerts(empresa)
        
        if alertas['total'] > 0:
            logger.info(f"Empresa {empresa.rut}: Se encontraron {alertas['total']} alertas. Enviando correo...")
            send_alert_email(empresa, alertas)
        else:
            logger.info(f"Empresa {empresa.rut}: Sin alertas pendientes.")

def get_empresa_alerts(empresa):
    now = timezone.now()
    fecha_limite_vencimiento = now.date() - timedelta(days=30)
    fecha_limite_sii = now - timedelta(hours=24) # Dar 24h de gracia para validar

    # 1. SII Pendiente: Estado 'procesado' pero validado_sii=False y creado hace más de 1 día
    sii_pending = Documento.objects.filter(
        empresa=empresa,
        estado='procesado',
        validado_sii=False,
        creado_en__lt=fecha_limite_sii
    ).order_by('fecha_emision')

    # 2. Vencidos: Fecha emisión hace más de 30 días y (opcional) no pagados
    # Nota: Ajusta el filtro si tienes un estado 'pagado'.
    vencidos = Documento.objects.filter(
        empresa=empresa,
        fecha_emision__lt=fecha_limite_vencimiento
    ).exclude(estado='error').order_by('fecha_emision')

    # 3. Errores: Documentos que fallaron el OCR
    errores = Documento.objects.filter(
        empresa=empresa,
        estado='error'
    ).order_by('-creado_en')

    return {
        'sii_pending': sii_pending,
        'vencidos': vencidos,
        'errores': errores,
        'total': sii_pending.count() + vencidos.count() + errores.count()
    }

def send_alert_email(empresa, alertas_data):
    try:
        # DEFINIR DESTINATARIO:
        # Opción A: Usar el email configurado en la empresa (email_user) si sirve de contacto.
        destinatario = empresa.email_user 
        
        # Opción B: Si tienes usuarios asociados a la empresa, úsalos:
        # destinatarios = [u.email for u in empresa.usuarios.all()]
        
        if not destinatario:
            logger.warning(f"Empresa {empresa.rut} tiene alertas pero no tiene email configurado.")
            return

        subject = f"⚠️ Alertas Pendientes SGIDT - {empresa.razon_social}"
        
        # Renderizamos el HTML que creaste en templates/correo/
        html_message = render_to_string('correo/alerta_documentos.html', {
            'empresa': empresa,
            'alertas': alertas_data,
            'total_alertas': alertas_data['total']
        })

        send_mail(
            subject=subject,
            message=f"Tienes {alertas_data['total']} alertas pendientes en el sistema.", # Fallback texto plano
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario], # Debe ser una lista
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Correo de alerta enviado a {destinatario}")

    except Exception as e:
        logger.error(f"Error enviando correo de alerta a empresa {empresa.id}: {e}")