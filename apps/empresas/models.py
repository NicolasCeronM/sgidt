from django.db import models
from django.conf import settings

# Create your models here.

class Empresa(models.Model):
    RAZONES_REGIMEN = (
        ("general", "Régimen general"),
        ("pyme", "Régimen Pro Pyme"),
        ("honorarios", "Honorarios / Persona natural"),  # por si quieres usarlo también
    )
    rut = models.CharField(max_length=12, unique=True)  # 76.123.456-7
    razon_social = models.CharField(max_length=255)
    giro = models.CharField(max_length=255, blank=True)
    regimen = models.CharField(max_length=20, choices=RAZONES_REGIMEN, default="pyme")
    direccion = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    contacto_email = models.EmailField(blank=True)
    contacto_telefono = models.CharField(max_length=20, blank=True)

    # dueño/creador de la empresa (no impide multiusuario más adelante)
    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="empresas_propias")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.razon_social} ({self.rut})"
