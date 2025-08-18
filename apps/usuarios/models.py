from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

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

    def __str__(self):
        return f"{self.username} ({self.rut})"
