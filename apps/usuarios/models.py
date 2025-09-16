from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

def user_avatar_upload_to(instance, filename):
    return f"usuarios/{instance.id or 'tmp'}/{filename}"

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
    # opcional: comuna, región
    comuna = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to=user_avatar_upload_to, blank=True, null=True)

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
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Reset {self.user} - {self.code}"