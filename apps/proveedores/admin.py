from django.contrib import admin
from .models import Proveedor, CategoriaProveedor, ProveedorContacto

# Register your models here.

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("razon_social","rut","giro","email","telefono","activo","categoria","owner")
    list_filter = ("activo","categoria","region","comuna")
    search_fields = ("razon_social","rut","giro","email","telefono","direccion")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)  # 👈 usuarios no ven ajenos

    def save_model(self, request, obj, form, change):
        if not change and not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
