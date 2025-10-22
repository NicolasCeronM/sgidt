from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .utils import clean_rut, is_valid_rut
from django.conf import settings


class CategoriaProveedor(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categoría de proveedor"
        verbose_name_plural = "Categorías de proveedores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    owner = models.ForeignKey(              # 👈 dueño del proveedor (usuario autenticado)
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proveedores"
    )
    razon_social = models.CharField(max_length=255)
    rut = models.CharField(max_length=12, help_text="Ej: 12345678-5")  # ya NO unique aquí
    giro = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=120, blank=True)
    region = models.CharField(max_length=120, blank=True)
    categoria = models.ForeignKey(CategoriaProveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name="proveedores")
    activo = models.BooleanField(default=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        unique_together = (("owner", "rut"),)        # 👈 rut único por usuario
        indexes = [
            models.Index(fields=["owner", "rut"]),   # 👈 búsquedas rápidas por usuario
            models.Index(fields=["owner", "razon_social"]),
        ]
        ordering = ["razon_social"]

    def clean(self):
        self.rut = clean_rut(self.rut)
        if self.rut and not is_valid_rut(self.rut):
            raise ValidationError({"rut": _("RUT inválido.")})

    def save(self, *args, **kwargs):
        self.rut = clean_rut(self.rut)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.razon_social} ({self.rut})"

class ProveedorContacto(models.Model):
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name="contactos"
    )
    nombre = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    cargo = models.CharField(max_length=120, blank=True)
    nota = models.TextField(blank=True)

    class Meta:
        verbose_name = "Contacto de proveedor"
        verbose_name_plural = "Contactos de proveedores"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.proveedor.razon_social}"
