from django.db import models
from django.conf import settings
from apps.empresas.models import Empresa
import hashlib
import mimetypes
from datetime import date

ESTADOS = (
("pendiente", "Pendiente"),
("procesando", "Procesando"),
("procesado", "Procesado"),
("error", "Error"),
)


TIPOS = (
("factura_afecta", "Factura Afecta"),
("factura_exenta", "Factura Exenta"),
("boleta_afecta", "Boleta Afecta"),
("boleta_exenta", "Boleta Exenta"),
("nota_credito", "Nota de Crédito"),
("desconocido", "Desconocido"),
)

def doc_upload_to(instance, filename):
    # media/documentos/<rut_empresa>/<año>/<mes>/<filename>
    year = date.today().year
    month = f"{date.today().month:02d}"
    rut_emp = (instance.empresa.rut if instance.empresa_id else "sin-empresa").replace(".", "")
    return f"documentos/{rut_emp}/{year}/{month}/{filename}"

class Documento(models.Model):
    # Archivo y metadatos
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="documentos")
    subido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="docs_subidos")
    archivo = models.FileField(upload_to=doc_upload_to)
    mime_type = models.CharField(max_length=120, blank=True)
    tamano_bytes = models.BigIntegerField(default=0)
    hash_sha256 = models.CharField(max_length=64, editable=False)


    # Extracción
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    tipo_documento = models.CharField(max_length=20, choices=TIPOS, default="desconocido")
    folio = models.CharField(max_length=30, blank=True)
    fecha_emision = models.DateField(null=True, blank=True)


    rut_proveedor = models.CharField(max_length=12, blank=True)
    razon_social_proveedor = models.CharField(max_length=255, blank=True)


    monto_neto = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monto_exento = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    iva = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)


    estado_sii = models.CharField(max_length=50, blank=True)
    ocr_json = models.JSONField(null=True, blank=True)


    creado_en = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ("-creado_en",)
        constraints = [
        models.UniqueConstraint(fields=("empresa", "hash_sha256"), name="uniq_doc_hash_empresa"),
        ]
        indexes = [
        models.Index(fields=["empresa", "rut_proveedor", "folio"]),
        ]


    def __str__(self):
        return f"{self.id} - {self.empresa} - {self.archivo.name}"


    def save(self, *args, **kwargs):
        # calcular hash/mime/tamaño cuando hay archivo nuevo
        if self.archivo and (not self.hash_sha256 or not self.tamano_bytes):
            sha = hashlib.sha256()
            for chunk in self.archivo.chunks():
                sha.update(chunk)
            self.hash_sha256 = sha.hexdigest()
            self.tamano_bytes = self.archivo.size or 0
            self.mime_type = mimetypes.guess_type(self.archivo.name)[0] or ""
        super().save(*args, **kwargs)