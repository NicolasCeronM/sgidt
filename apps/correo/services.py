# apps/correo/services.py
# (Los imports y la función decode_subject se mantienen igual)
import imaplib
import email
from email.header import decode_header
import logging
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Correo, Adjunto
from apps.empresas.models import Empresa
from apps.documentos.services.upload_service import handle_uploaded_file

logger = logging.getLogger(__name__)

ALLOWED_SUBJECTS = ['factura', 'dte', 'documento tributario', 'comprobante']

def decode_subject(header):
    if header is None: return ""
    decoded_parts = decode_header(header)
    subject = []
    for part, charset in decoded_parts:
        try:
            if isinstance(part, bytes):
                subject.append(part.decode(charset or 'utf-8', 'ignore'))
            else:
                subject.append(str(part))
        except LookupError:
            logger.warning(f"Codificación desconocida '{charset}' en el asunto.")
            subject.append(str(part))
    return "".join(subject)


def get_unread_email_ids(empresa: Empresa) -> list[bytes]:
    """
    Se conecta al correo y devuelve solo la lista de IDs de correos no leídos.
    """
    if not all([empresa.email_host, empresa.email_user, empresa.email_password]):
        return []
    
    mail = None
    try:
        if empresa.email_use_ssl:
            mail = imaplib.IMAP4_SSL(empresa.email_host, empresa.email_port)
        else:
            mail = imaplib.IMAP4(empresa.email_host, empresa.email_port)
        
        mail.login(empresa.email_user, empresa.email_password)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return []
        
        return messages[0].split()
    finally:
        if mail:
            if mail.state == 'SELECTED': mail.close()
            mail.logout()


def process_email_batch_from_ids(empresa: Empresa, email_ids: list[bytes]):
    """
    Procesa un lote específico de correos.
    """
    if not email_ids: return
    
    mail = None
    try:
        if empresa.email_use_ssl:
            mail = imaplib.IMAP4_SSL(empresa.email_host, empresa.email_port)
        else:
            mail = imaplib.IMAP4(empresa.email_host, empresa.email_port)
            
        mail.login(empresa.email_user, empresa.email_password)
        mail.select("inbox")

        logger.info(f"Procesando un lote de {len(email_ids)} correos para {empresa.rut}.")

        for email_id in email_ids:
            try:
                # Obtenemos solo las cabeceras para filtrar
                status, msg_data = mail.fetch(email_id, "(BODY[HEADER.FIELDS (SUBJECT)])")
                if status != "OK": continue

                header_msg = email.message_from_bytes(msg_data[0][1])
                subject = decode_subject(header_msg.get('subject')).lower()

                # Si el asunto coincide, procesamos el correo completo
                if any(keyword in subject for keyword in ALLOWED_SUBJECTS):
                    logger.info(f"  > Asunto '{subject}' coincide. Procesando...")
                    process_single_email(mail, email_id, empresa)
                
                # Siempre marcamos como leído
                mail.store(email_id, '+FLAGS', '\\Seen')
            except Exception as e:
                logger.error(f"Error procesando el correo ID {email_id.decode()}: {e}")
                mail.store(email_id, '+FLAGS', '\\Seen')

        empresa.email_last_check = timezone.now()
        empresa.save(update_fields=["email_last_check"])
    finally:
        if mail:
            if mail.state == 'SELECTED': mail.close()
            mail.logout()

def process_single_email(mail_server, email_id, empresa: Empresa):
    # (Esta función no necesita cambios, se mantiene igual que en la respuesta anterior)
    # ...
    status, msg_data = mail_server.fetch(email_id, "(RFC822)")
    if status != "OK":
        logger.warning(f"No se pudo obtener el correo con ID {email_id.decode()}.")
        return

    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            
            msg_uid = email_id.decode()
            if Correo.objects.filter(empresa=empresa, msg_uid=msg_uid).exists():
                logger.info(f"Correo {msg_uid} ya fue procesado anteriormente. Omitiendo.")
                return

            correo_obj = Correo.objects.create(
                empresa=empresa,
                msg_uid=msg_uid,
                asunto=decode_subject(msg["Subject"]),
                remitente=msg.get("From"),
                fecha=timezone.now()
            )
            logger.info(f"Procesando correo de '{correo_obj.remitente}' con asunto '{correo_obj.asunto}'")

            for part in msg.walk():
                if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if filename:
                    logger.info(f"  > Adjunto encontrado: {filename}")
                    
                    if filename.lower().endswith(('.pdf', '.xml')):
                        logger.info(f"    - Es un archivo de factura válido. Procesando...")
                        file_data = part.get_payload(decode=True)
                        
                        adjunto = Adjunto.objects.create(
                            correo=correo_obj,
                            nombre_archivo=filename,
                            content_type=part.get_content_type()
                        )
                        adjunto.archivo.save(filename, ContentFile(file_data), save=True)

                        try:
                            documento = handle_uploaded_file(adjunto.archivo, empresa, origen="email")
                            if documento:
                                adjunto.documento_procesado = documento
                                adjunto.save(update_fields=["documento_procesado"])
                                logger.info(f"    - ¡ÉXITO! Documento {documento.id} creado desde {filename}.")
                            else:
                                logger.warning(f"    - ADVERTENCIA: handle_uploaded_file no devolvió un documento para {filename}.")
                        except Exception as e:
                            logger.error(f"    - ERROR al crear Documento desde adjunto {filename}: {e}", exc_info=True)
                    else:
                        logger.info(f"    - Omitiendo adjunto (no es PDF ni XML).")