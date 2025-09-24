from django.contrib import admin
from .models import SIITransaccion, SIIContribuyenteCache

# Register your models here.

@admin.register(SIITransaccion)
class SIITransaccionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "empresa", "endpoint", "track_id", "ok", "estado", "status_code")
    list_filter = ("endpoint", "ok", "estado", "created_at", "empresa")
    search_fields = ("track_id", "request_payload", "response_payload")

@admin.register(SIIContribuyenteCache)
class SIIContribuyenteCacheAdmin(admin.ModelAdmin):
    list_display = ("rut", "razon_social", "estado", "refreshed_at")
    search_fields = ("rut", "razon_social")
