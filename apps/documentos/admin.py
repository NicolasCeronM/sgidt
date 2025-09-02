from django.contrib import admin
from apps.documentos.models import Documento

# Register your models here.

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "id", "empresa", "tipo_documento", "folio",
        "rut_proveedor", "razon_social_proveedor",
        "fecha_emision", "total", "estado",  
        "creado_en",
    )
    list_filter = (
        "empresa", "tipo_documento", "estado",  
        "fecha_emision", "creado_en",
    )
    search_fields = ("folio", "rut_proveedor", "razon_social_proveedor", "archivo")
    readonly_fields = ("hash_sha256", "mime_type", "tamano_bytes", "creado_en", "ocr_json")
    date_hierarchy = "fecha_emision"
    ordering = ("-creado_en",)