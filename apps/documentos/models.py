from django.db import models
from django.conf import settings
from apps.empresas.models import Empresa
import hashlib
import mimetypes
from datetime import date

# Create your models here.

def doc_upload_to(instance, filename):
    # media/documentos/<rut_empresa>/<año>/<mes>/<filename>
    year = date.today().year
    month = f"{date.today().month:02d}"
    rut_emp = (instance.empresa.rut if instance.empresa_id else "sin-empresa").replace(".", "")
    return f"documentos/{rut_emp}/{year}/{month}/{filename}"

class Documento(models.Model):
    TIPO_DOC = (
        ("factura_afecta", "Factura afecta"),
        ("factura_exenta", "Factura exenta"),
        ("boleta", "Boleta"),
        ("nota_credito", "Nota de crédito"),
    )
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="documentos")
    subido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="docs_subidos")

    archivo = models.FileField(upload_to=doc_upload_to)
    hash_sha256 = models.CharField(max_length=64, db_index=True, editable=False)
    mime_type = models.CharField(max_length=100, blank=True, editable=False)
    tamano_bytes = models.PositiveBigIntegerField(default=0, editable=False)

    # metadatos (se llenarán luego por OCR o manual)
    tipo = models.CharField(max_length=20, choices=TIPO_DOC, blank=True)
    proveedor = models.CharField(max_length=255, blank=True)
    rut_proveedor = models.CharField(max_length=12, blank=True)
    folio = models.CharField(max_length=30, blank=True)
    fecha_emision = models.DateField(null=True, blank=True)

    neto = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    iva = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    estado_sii = models.CharField(max_length=50, blank=True)  # “Vigente/Anulada” (luego validación real)
    ocr_json = models.JSONField(null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-creado_en",)
        indexes = [
            models.Index(fields=["empresa", "rut_proveedor", "folio"]),
        ]
        constraints = [
            # Evita subir 2 veces el mismo archivo (por hash)
            models.UniqueConstraint(fields=["empresa", "hash_sha256"], name="uniq_doc_hash_empresa"),
        ]

    def __str__(self):
        return f"{self.id} - {self.empresa} - {self.archivo.name}"

    def save(self, *args, **kwargs):
        # calcular hash/mime/tamaño cuando hay archivo nuevo
        if self.archivo and (not self.hash_sha256 or not self.tamano_bytes):
            # lee en bloques para no reventar memoria
            sha = hashlib.sha256()
            for chunk in self.archivo.chunks():
                sha.update(chunk)
            self.hash_sha256 = sha.hexdigest()
            self.tamano_bytes = self.archivo.size or 0
            self.mime_type = mimetypes.guess_type(self.archivo.name)[0] or ""
        super().save(*args, **kwargs)
