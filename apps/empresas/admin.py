from django.contrib import admin
from .models import Empresa

# Register your models here.

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "rut", "propietario", "created_at")
    list_filter = ("created_at",)
    search_fields = ("razon_social", "rut")
    ordering = ("razon_social",)
