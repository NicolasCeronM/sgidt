# apps/correo/models.py

from django.db import models
from apps.empresas.models import Empresa
from apps.documentos.models import Documento # Para vincular el adjunto al documento procesado

def email_attachment_path(instance, filename):
    return f"empresas/{instance.correo.empresa.id}/correos/{instance.correo.id}/{filename}"

class Correo(models.Model):
    """ Almacena la metadata de un correo electrónico procesado. """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="correos")
    msg_uid = models.CharField(max_length=255, help_text="UID único del mensaje en el servidor de correo")
    asunto = models.CharField(max_length=512)
    remitente = models.CharField(max_length=255)
    fecha = models.DateTimeField()
    procesado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('empresa', 'msg_uid')
        ordering = ['-fecha']

    def __str__(self):
        return f"Correo de {self.remitente} - {self.asunto}"

class Adjunto(models.Model):
    """ Guarda un archivo adjunto de un correo. """
    correo = models.ForeignKey(Correo, on_delete=models.CASCADE, related_name="adjuntos")
    archivo = models.FileField(upload_to=email_attachment_path)
    nombre_archivo = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    
    # Vincula el adjunto con el documento que se creó a partir de él.
    documento_procesado = models.OneToOneField(
        Documento, on_delete=models.SET_NULL, null=True, blank=True, related_name="adjunto_origen"
    )

    def __str__(self):
        return self.nombre_archivo