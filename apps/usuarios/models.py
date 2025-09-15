from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone as dj_timezone

# Modelo personalizado de usuario
class Usuario(AbstractUser):
    TIPO_CONTRIBUYENTE = (
        ("empresa", "Empresa"),
        ("persona", "Persona natural"),
    )
    tipo_contribuyente = models.CharField(max_length=10, choices=TIPO_CONTRIBUYENTE)
    email = models.EmailField(unique=True)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    comuna = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.username} ({self.rut})"


# Modelo para manejar códigos de restablecimiento de contraseña
class PasswordResetCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reset_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    requester_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "code"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["is_used"]),
        ]

    def is_expired(self):
        return dj_timezone.now() >= self.expires_at

    def __str__(self):
        return f"Reset {self.user} - {self.code}"


# Modelo para perfil extendido del usuario
User = settings.AUTH_USER_MODEL

def company_logo_upload_to(instance, filename):
    return f"companies/{instance.user_id}/logo/{filename}"

def avatar_upload_to(instance, filename):
    return f"users/{instance.user_id}/avatar/{filename}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # ---- Datos personales ----
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True)
    cargo = models.CharField(max_length=80, blank=True)
    time_zone = models.CharField(max_length=64, default="America/Santiago")  # <- corregido
    idioma_pref = models.CharField(
        max_length=5,
        choices=[("es", "Español"), ("en", "English"), ("pt", "Português")],
        default="es",
    )

    # ---- Datos PYME ----
    empresa_nombre = models.CharField("Razón social", max_length=160, blank=True)
    empresa_fantasia = models.CharField("Nombre de fantasía", max_length=160, blank=True)
    empresa_rut = models.CharField("RUT", max_length=20, blank=True)
    empresa_giro = models.CharField("Giro", max_length=160, blank=True)

    empresa_telefono = models.CharField(max_length=30, blank=True)
    empresa_email = models.EmailField(blank=True)
    empresa_web = models.URLField(blank=True)

    empresa_region = models.CharField(max_length=100, blank=True)
    empresa_comuna = models.CharField(max_length=100, blank=True)
    empresa_direccion = models.CharField(max_length=220, blank=True)
    empresa_logo = models.ImageField(upload_to=company_logo_upload_to, blank=True, null=True)
    color_primario = models.CharField(max_length=7, blank=True, help_text="#E2261C")
    color_secundario = models.CharField(max_length=7, blank=True, help_text="#232323")

    # ---- Preferencias del sistema ----
    notificaciones_email = models.BooleanField(default=True)
    notificaciones_whatsapp = models.BooleanField(default=False)
    recibe_boletin = models.BooleanField(default=False)

    # ---- Facturación / preferencias tributarias (opcional) ----
    sii_regimen = models.CharField(max_length=80, blank=True, help_text="Ej: ProPyme, 14D3, 14A, etc.")
    sii_actividad = models.CharField(max_length=160, blank=True)
    sii_cod_sii = models.CharField("Cód. actividad SII", max_length=12, blank=True)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=dj_timezone.now)  # <- corregido

    def __str__(self):
        return f"Perfil de {self.user}"
