from __future__ import annotations
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, EmailValidator, RegexValidator
from django.db import models
from .models_contribuyente import Contribuyente

def empresa_logo_upload_to(instance, filename):
    return f"empresas/{instance.id or 'tmp'}/{filename}"
# -----------------------------
# Utilidades Chile: RUT
# -----------------------------
RUT_FORMAT_RE = RegexValidator(
    regex=r"^[0-9]{1,8}-[0-9Kk]$",
    message="RUT inválido. Formato esperado: ########-K",
)

def normalizar_rut(rut: str) -> str:
    """
    Limpia puntos/espacios, pone guión y DV mayúscula.
    Acepta '12.345.678-k', '12345678k', etc.
    """
    if not rut:
        return rut
    clean = "".join(ch for ch in rut if ch.isalnum())
    if len(clean) < 2:
        return rut
    cuerpo, dv = clean[:-1], clean[-1].upper()
    return f"{int(cuerpo)}-{dv}"

def validar_rut(rut: str) -> None:
    """
    Valida DV (módulo 11). Lanza ValidationError si no es válido.
    """
    if not rut:
        raise ValidationError("RUT requerido.")
    RUT_FORMAT_RE(rut)
    cuerpo, dv = rut.split("-")
    acum, mult = 0, 2
    for c in reversed(cuerpo):
        acum += int(c) * mult
        mult = 2 if mult == 7 else mult + 1
    resto = 11 - (acum % 11)
    dv_calc = "0" if resto == 11 else "K" if resto == 10 else str(resto)
    if dv_calc != dv.upper():
        raise ValidationError("RUT inválido (DV no coincide).")


# -----------------------------
# Catálogos / Choices
# -----------------------------
class RegimenTributario(models.TextChoices):
    PYME_TRASPARENTE = "14D8", "Pro PyME Transparente (14 D 8)"
    PYME_GENERAL     = "14D3", "Pro PyME General (14 D 3)"
    GENERAL          = "GEN",  "Régimen General"
    PRIMERA_CATEGORIA = "PCAT", "Régimen Primera Categoría"
    SEGUNDA_CATEGORIA = "SCAT", "Régimen Segunda Categoría"

class TipoSocietario(models.TextChoices):
    PERSONA_NATURAL = "PN",   "Persona Natural con Giro"
    EIRL            = "EIRL", "E.I.R.L."
    SPA             = "SPA",  "SpA"
    LTDA            = "LTDA", "Limitada"
    SA              = "SA",   "S.A."
    OTRO            = "OTRO", "Otro"

class RolEmpresa(models.TextChoices):
    ADMIN    = "admin",    "Administrador"
    CONTADOR = "contador", "Contador"
    ANALISTA = "analista", "Analista"


# -----------------------------
# Modelo principal: Empresa
# -----------------------------
class Empresa(models.Model):
    # Identificación SII
    rut = models.CharField(
        max_length=12, unique=True,
        help_text="RUT con guión (ej: 76262345-K)"
    )
    razon_social = models.CharField(
        max_length=255,
        help_text="Nombre o razón social inscrita en SII"
    )
    giro = models.CharField(max_length=255, blank=True)
    codigo_actividad = models.CharField(max_length=6, blank=True)
    tipo_societario = models.CharField(
        max_length=10, choices=TipoSocietario.choices, default=TipoSocietario.SPA
    )
    regimen_tributario = models.CharField(
        max_length=4, choices=RegimenTributario.choices, default=RegimenTributario.PYME_GENERAL
    )
    fecha_inicio_actividades = models.DateField(null=True, blank=True)

    contribuyente = models.OneToOneField(
        Contribuyente,
        on_delete=models.PROTECT,
        related_name="empresa",
        null=True,
        blank=True
    )

    # Contacto / domicilio
    email = models.EmailField(validators=[EmailValidator()], blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=80, blank=True)
    region = models.CharField(max_length=80, blank=True)

    # Métrica para clasificar PyME
    ingresos_12m_uf = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text="Ingresos por ventas últimos 12 meses (en UF)"
    )
    logo = models.ImageField(upload_to=empresa_logo_upload_to, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["rut"]),
            models.Index(fields=["razon_social"]),
        ]
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    @property
    def nombre(self) -> str:
        """Alias para plantillas: {{ empresa.nombre }}"""
        return self.razon_social

    @property
    def clasificacion_pyme(self) -> str:
        v = float(self.ingresos_12m_uf or 0)
        if v <= 2400:
            return "Microempresa"
        if 2400 < v <= 25000:
            return "Pequeña"
        if 25000 < v <= 100000:
            return "Mediana"
        return "Gran empresa"

    def clean(self):
        if self.rut:
            self.rut = normalizar_rut(self.rut)
            validar_rut(self.rut)

    def __str__(self) -> str:
        return f"{self.razon_social} ({self.rut})"


# -----------------------------
# Membresía usuario <-> empresa
# -----------------------------
class EmpresaUsuario(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="empresas"
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, related_name="miembros"
    )
    rol = models.CharField(max_length=20, choices=RolEmpresa.choices, default=RolEmpresa.ADMIN)
    creado_en = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        unique_together = ("usuario", "empresa")
        verbose_name = "Membresía de Empresa"
        verbose_name_plural = "Membresías de Empresa"

    def __str__(self) -> str:
        return f"{self.usuario} @ {self.empresa} ({self.rol})"
