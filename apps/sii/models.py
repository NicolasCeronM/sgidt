from django.db import models
from django.utils import timezone

# Ajusta el import al módulo donde declaraste Empresa.
# Si tu app de empresas se llama "apps.empresas", cambia la ruta:
from apps.empresas.models import Empresa  # <- ajusta este import a tu proyecto

class SIITransaccion(models.Model):
    ENDPOINT_CHOICES = [
        ("contribuyente", "Consulta contribuyente"),
        ("validar_dte",   "Validar DTE"),
        ("estado_dte",    "Estado DTE"),
        ("recibir_dte",   "Recibir DTE"),
    ]
    empresa = models.ForeignKey(
        Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name="sii_transacciones"
    )
    endpoint = models.CharField(max_length=32, choices=ENDPOINT_CHOICES)
    track_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    estado = models.CharField(max_length=32, null=True, blank=True, db_index=True)  # ACEPTADO/RECHAZADO/RECIBIDO/...
    ok = models.BooleanField(default=True)
    status_code = models.PositiveSmallIntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["endpoint", "created_at"]),
            models.Index(fields=["track_id"]),
            models.Index(fields=["estado"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.endpoint} [{self.track_id or '-'}] {self.created_at:%Y-%m-%d %H:%M}"


class SIIContribuyenteCache(models.Model):
    rut = models.CharField(max_length=16, unique=True, db_index=True)
    razon_social = models.CharField(max_length=255)
    actividad_principal = models.CharField(max_length=255)
    estado = models.CharField(max_length=32)  # ACTIVO/SUSPENDIDO
    refreshed_at = models.DateTimeField(auto_now=True)  # TTL simple

    def is_fresh(self, minutes=30) -> bool:
        return (timezone.now() - self.refreshed_at).total_seconds() < minutes * 60

    def __str__(self):
        return f"{self.rut} - {self.razon_social}"
