from django.db import models
from django.conf import settings
from django.db.models import Q
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
    today = date.today()
    year = today.year
    month = f"{today.month:02d}"
    rut_emp = (instance.empresa.rut if instance.empresa_id else "sin-empresa").replace(".", "")
    return f"documentos/{rut_emp}/{year}/{month}/{filename}"

class Documento(models.Model):
    # --- Archivo y metadatos ---
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="documentos")
    subido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="docs_subidos")

    archivo = models.FileField(upload_to=doc_upload_to)
    nombre_archivo_original = models.CharField(max_length=255, blank=True)
    extension = models.CharField(max_length=10, blank=True)
    es_pdf = models.BooleanField(default=False)
    origen = models.CharField(max_length=20, default='web', db_index=True)

    mime_type = models.CharField(max_length=120, blank=True)
    tamano_bytes = models.BigIntegerField(default=0)
    hash_sha256 = models.CharField(max_length=64, editable=False)

    paginas = models.PositiveIntegerField(null=True, blank=True)  # para PDFs
    texto_plano = models.TextField(blank=True, default="")

    # --- Extracción (OCR/parse) ---
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    tipo_documento = models.CharField(max_length=50, choices=TIPOS, default="desconocido")

    folio = models.CharField(max_length=30, blank=True)
    fecha_emision = models.DateField(null=True, blank=True)

    rut_proveedor = models.CharField(max_length=12, blank=True)  # normalizado con dv
    razon_social_proveedor = models.CharField(max_length=255, blank=True)

    # Montos (CLP o con decimales si corresponde)
    monto_neto = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monto_exento = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    iva = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Tributario adicional
    iva_tasa = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # p.ej. 19.00, 0.00

    # Validación SII
    validado_sii = models.BooleanField(default=False)
    sii_track_id = models.CharField(max_length=64, blank=True)
    sii_estado = models.CharField(max_length=50, blank=True)     # p.ej. 'ACEPTADO', 'RECHAZADO', 'PENDIENTE'
    sii_glosa = models.CharField(max_length=255, blank=True)
    sii_validado_en = models.DateTimeField(null=True, blank=True)

    # Auditoría OCR
    ocr_fuente = models.CharField(max_length=20, blank=True)     # 'pdf_text', 'pdf_ocr', 'image_ocr'
    ocr_lang = models.CharField(max_length=30, blank=True)       # 'spa+eng'
    ocr_engine = models.CharField(max_length=50, blank=True)     # 'tesseract'
    ocr_version = models.CharField(max_length=20, blank=True)    # '5.3.0'
    ocr_json = models.JSONField(null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-creado_en",)
        constraints = [
            # Evita cargas binariamente duplicadas por empresa
            models.UniqueConstraint(fields=("empresa", "hash_sha256"), name="uniq_doc_hash_empresa"),

            # Evita duplicar un mismo folio del mismo proveedor y tipo para esa empresa
            models.UniqueConstraint(
                fields=("empresa", "rut_proveedor", "tipo_documento", "folio"),
                name="uniq_doc_folio_empresa_proveedor_tipo",
                condition=Q(folio__gt="")  # solo aplica si viene folio
            ),
        ]
        indexes = [
            models.Index(fields=["empresa", "rut_proveedor", "folio"]),
            models.Index(fields=["empresa", "fecha_emision"]),
            models.Index(fields=["empresa", "tipo_documento"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["creado_en"]),
        ]

    def __str__(self):
        return f"{self.id} - {self.empresa} - {self.archivo.name}"

    def save(self, *args, **kwargs):
        # calcular hash/mime/tamaño/extension/es_pdf al cargar o cambiar archivo
        if self.archivo and (not self.hash_sha256 or not self.tamano_bytes or not self.mime_type):
            sha = hashlib.sha256()
            for chunk in self.archivo.chunks():
                sha.update(chunk)
            self.hash_sha256 = sha.hexdigest()
            self.tamano_bytes = self.archivo.size or 0
            self.mime_type = mimetypes.guess_type(self.archivo.name)[0] or ""
            self.extension = (self.archivo.name.split(".")[-1] or "").lower()
            self.es_pdf = self.extension == "pdf"
            if not self.nombre_archivo_original:
                self.nombre_archivo_original = self.archivo.name
        super().save(*args, **kwargs)
