# apps/Empresa/admin_contribuyente.py
from django.contrib import admin
from .models_contribuyente import Contribuyente, TipoContribuyente

@admin.register(Contribuyente)
class ContribuyenteAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "rut", "tipo", "habilitado_dte", "solo_honorarios", "creado_en")
    list_filter = ("tipo", "habilitado_dte", "solo_honorarios")
    search_fields = ("razon_social", "rut")
    readonly_fields = ("creado_en", "actualizado_en")
