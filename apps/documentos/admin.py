from django.contrib import admin
from .models import Documento

# Register your models here.

# @admin.register(Documento)
# class DocumentoAdmin(admin.ModelAdmin):
#     list_display = ("id","empresa","tipo","rut_proveedor","folio","total","creado_en")
#     list_filter = ("empresa","tipo","creado_en")
#     search_fields = ("folio","rut_proveedor","proveedor","archivo")
#     readonly_fields = ("hash_sha256","mime_type","tamano_bytes","creado_en")
