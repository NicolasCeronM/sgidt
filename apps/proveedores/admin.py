from django.contrib import admin
from .models import Proveedor, CategoriaProveedor, ProveedorContacto

# Register your models here.

@admin.register(CategoriaProveedor)
class CategoriaProveedorAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)


class ProveedorContactoInline(admin.TabularInline):
    model = ProveedorContacto
    extra = 0


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "rut", "giro", "email", "telefono", "activo", "categoria")
    list_filter = ("activo", "categoria", "region", "comuna")
    search_fields = ("razon_social", "rut", "giro", "email", "telefono", "direccion")
    inlines = [ProveedorContactoInline]