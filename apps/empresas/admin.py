from django.contrib import admin
from .models import Empresa

# Register your models here.

from django.contrib import admin
from .models import Empresa, EmpresaUsuario

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "rut", "regimen_tributario", "clasificacion_pyme", "actualizado_en")
    search_fields = ("razon_social", "rut")
    list_filter = ("regimen_tributario", "region")

@admin.register(EmpresaUsuario)
class EmpresaUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "empresa", "rol", "creado_en")
    search_fields = ("usuario__email", "empresa__razon_social")
    list_filter = ("rol",)
