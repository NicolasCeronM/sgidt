# apps/Empresa/models_contribuyente.py
from django.db import models
from django.core.exceptions import ValidationError

# -------------------------------------------------------------------
# RUT helpers
# - Intentamos reutilizar tus funciones si ya existen en tu proyecto.
# - Si no existen, usamos fallbacks internos seguros para producción.
# -------------------------------------------------------------------
def _fallback_normalizar_rut(rut: str) -> str:
    if not rut:
        return rut
    rut = rut.replace(".", "").replace("-", "").strip().upper()
    if len(rut) < 2:
        return rut
    cuerpo, dv = rut[:-1], rut[-1]
    # formatea como 99999999-DV
    return f"{cuerpo}-{dv}"

def _fallback_validar_rut(rut: str) -> None:
    if not rut:
        raise ValidationError("RUT vacío.")
    val = rut.replace(".", "").replace("-", "").strip().upper()
    if len(val) < 2:
        raise ValidationError("RUT inválido.")
    cuerpo, dv = val[:-1], val[-1]
    if not cuerpo.isdigit():
        raise ValidationError("RUT inválido.")
    # módulo 11
    suma = 0
    factor = 2
    for c in reversed(cuerpo):
        suma += int(c) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = suma % 11
    dv_calc = 11 - resto
    if dv_calc == 11:
        dv_calc_chr = "0"
    elif dv_calc == 10:
        dv_calc_chr = "K"
    else:
        dv_calc_chr = str(dv_calc)
    if dv != dv_calc_chr:
        raise ValidationError("RUT inválido (DV no coincide).")

# Intenta importar tus helpers reales si existen
try:
    # Ajusta el import si tus helpers están en otro módulo
    from .models import normalizar_rut as _rut_normalizar
    from .models import validar_rut as _rut_validar
except Exception:
    _rut_normalizar = _fallback_normalizar_rut
    _rut_validar = _fallback_validar_rut


# -------------------------------------------------------------------
# Enumeración de tipos de contribuyente
# -------------------------------------------------------------------
class TipoContribuyente(models.TextChoices):
    PN_HONORARIOS = "PN_HONORARIOS", "Persona natural - honorarios"
    PN_GIRO = "PN_GIRO", "Persona natural con giro (1ª cat.)"
    PJ = "PJ", "Persona jurídica (PyME)"


# -------------------------------------------------------------------
# Modelo Contribuyente
# -------------------------------------------------------------------
class Contribuyente(models.Model):
    tipo = models.CharField(max_length=20, choices=TipoContribuyente.choices)

    # Identificación tributaria
    rut = models.CharField(max_length=12, unique=True)  # normalizado: 99999999-K
    razon_social = models.CharField(max_length=255)     # nombre completo o razón social
    nombre_fantasia = models.CharField(max_length=255, blank=True)

    # Datos SII
    actividad_economica = models.CharField(max_length=10, blank=True)
    fecha_inicio_actividades = models.DateField(null=True, blank=True)
    domicilio_calle = models.CharField(max_length=255, blank=True)
    domicilio_numero = models.CharField(max_length=20, blank=True)
    domicilio_comuna = models.CharField(max_length=100, blank=True)
    domicilio_region = models.CharField(max_length=100, blank=True)

    # Emisión / DTE
    sistema_facturacion = models.CharField(
        max_length=20,
        choices=[("SII_GRATIS", "SII_GRATIS"), ("MERCADO", "MERCADO")],
        blank=True
    )
    certificado_usa = models.BooleanField(default=False)     # True si usa sistema de mercado
    tipos_dte_autorizados = models.JSONField(default=list, blank=True)  # p.ej. [33,34,39,41,56,61,52]

    # Flags tributarios
    habilitado_dte = models.BooleanField(default=False)      # emite DTE (1ª categoría)
    solo_honorarios = models.BooleanField(default=False)     # solo BHE (2ª categoría)
    tasa_retencion_honorarios = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Representación (solo PJ)
    rep_rut = models.CharField(max_length=12, blank=True)
    rep_nombre = models.CharField(max_length=255, blank=True)

    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contribuyente"
        verbose_name_plural = "Contribuyentes"

    # ----------------------
    # Validaciones de dominio
    # ----------------------
    def clean(self):
        # Normaliza y valida RUT
        self.rut = _rut_normalizar(self.rut)
        _rut_validar(self.rut)

        # Reglas por tipo
        if self.tipo == TipoContribuyente.PN_HONORARIOS:
            # No puede advertir DTE en PN honorarios
            if self.tipos_dte_autorizados:
                raise ValidationError("PN honorarios no puede tener DTE autorizados.")
            self.habilitado_dte = False
            self.solo_honorarios = True
            # La tasa puede setearse por default en signals o formulario si no viene

        if self.tipo == TipoContribuyente.PJ:
            if not self.rep_rut or not self.rep_nombre:
                raise ValidationError("Persona jurídica requiere representante (RUT y nombre).")

    def save(self, *args, **kwargs):
        # Garantiza validaciones al guardar desde admin y code
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.razon_social} ({self.rut}) [{self.get_tipo_display()}]"
