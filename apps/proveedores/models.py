from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .utils import clean_rut, is_valid_rut


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
    razon_social = models.CharField(max_length=255)
    rut = models.CharField(
        max_length=12,
        unique=True,  # 👈 cada RUT debe ser único
        help_text="Ej: 12345678-5"
    )
    giro = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=120, blank=True)
    region = models.CharField(max_length=120, blank=True)
    categoria = models.ForeignKey(
        CategoriaProveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="proveedores"
    )
    activo = models.BooleanField(default=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        indexes = [
            models.Index(fields=["rut"]),
            models.Index(fields=["razon_social"]),
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
