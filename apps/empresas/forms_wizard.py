# apps/Empresa/forms_wizard.py
from django import forms
from django.core.exceptions import ValidationError

from .models_contribuyente import TipoContribuyente
from .models_contribuyente import Contribuyente as ContribuyenteModel

# Intenta reutilizar tus helpers de RUT
try:
    from .models import normalizar_rut, validar_rut
except Exception:
    # Fallbacks mínimos
    def normalizar_rut(rut: str) -> str:
        if not rut:
            return rut
        r = rut.replace(".", "").replace("-", "").strip().upper()
        if len(r) < 2:
            return rut
        return f"{r[:-1]}-{r[-1]}"

    def validar_rut(rut: str) -> None:
        if not rut:
            raise ValidationError("RUT vacío.")
        v = rut.replace(".", "").replace("-", "").strip().upper()
        if len(v) < 2 or not v[:-1].isdigit():
            raise ValidationError("RUT inválido.")
        cuerpo, dv = v[:-1], v[-1]
        suma, factor = 0, 2
        for c in reversed(cuerpo):
            suma += int(c) * factor
            factor = 2 if factor == 7 else factor + 1
        resto = suma % 11
        dv_calc = 11 - resto
        dv_calc_chr = "0" if dv_calc == 11 else ("K" if dv_calc == 10 else str(dv_calc))
        if dv != dv_calc_chr:
            raise ValidationError("RUT inválido (DV no coincide).")


class Paso1TipoForm(forms.Form):
    tipo = forms.ChoiceField(
        choices=TipoContribuyente.choices,
        widget=forms.RadioSelect,
        label="Selecciona el tipo de contribuyente"
    )


class Paso2IdentificacionForm(forms.Form):
    rut = forms.CharField(label="RUT (con DV)", max_length=12)
    razon_social = forms.CharField(label="Nombre / Razón social", max_length=255)
    nombre_fantasia = forms.CharField(label="Nombre de fantasía", max_length=255, required=False)

    def clean_rut(self):
        rut = normalizar_rut(self.cleaned_data["rut"])
        validar_rut(rut)
        # verifica unicidad a nivel Contribuyente (si se creará uno nuevo)
        if ContribuyenteModel.objects.filter(rut=rut).exists():
            raise ValidationError("Ya existe un contribuyente con este RUT.")
        return rut


class Paso3DatosTributariosForm(forms.Form):
    actividad_economica = forms.CharField(max_length=10, required=False, help_text="Código SII (opcional)")
    fecha_inicio_actividades = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Si la conoces"
    )
    domicilio_calle = forms.CharField(max_length=255, required=False)
    domicilio_numero = forms.CharField(max_length=20, required=False)
    domicilio_comuna = forms.CharField(max_length=100, required=False)
    domicilio_region = forms.CharField(max_length=100, required=False)


class Paso4EmisionForm(forms.Form):
    sistema_facturacion = forms.ChoiceField(
        choices=[("", "------"), ("SII_GRATIS", "SII_GRATIS"), ("MERCADO", "MERCADO")],
        required=False,
        label="Sistema de emisión"
    )
    certificado_usa = forms.BooleanField(required=False, label="Usará certificado digital (sistemas de mercado)")
    tipos_dte_autorizados = forms.CharField(required=False, help_text="Ejemplo: 33,34,39,41,56,61,52")
    tasa_retencion_honorarios = forms.DecimalField(required=False, max_digits=5, decimal_places=2,
                                                   help_text="Solo para PN honorarios (ej: 14.5 en 2025)")

    def __init__(self, *args, **kwargs):
        self.tipo_actual = kwargs.pop("tipo_actual", None)
        super().__init__(*args, **kwargs)

        if self.tipo_actual == "PN_HONORARIOS":
            # Oculta controles de DTE
            self.fields["sistema_facturacion"].widget = forms.HiddenInput()
            self.fields["certificado_usa"].widget = forms.HiddenInput()
            self.fields["tipos_dte_autorizados"].widget = forms.HiddenInput()

            # No marcar required, lo validamos en clean
            self.fields["tasa_retencion_honorarios"].required = False
            if not self.initial.get("tasa_retencion_honorarios"):
                self.initial["tasa_retencion_honorarios"] = 14.5
        else:
            self.fields["sistema_facturacion"].required = True

    def clean(self):
        data = super().clean()
        # Normaliza DTE
        raw = (data.get("tipos_dte_autorizados") or "").strip()
        dtes = []
        if raw:
            try:
                dtes = [int(x.strip()) for x in raw.split(",") if x.strip()]
            except Exception:
                self.add_error("tipos_dte_autorizados", "Formato inválido. Usa coma: 33,34,39")
        data["tipos_dte_autorizados"] = dtes

        # Reglas por tipo
        if self.tipo_actual == "PN_HONORARIOS":
            data["tipos_dte_autorizados"] = []
            data["sistema_facturacion"] = ""
            data["certificado_usa"] = False
            if not data.get("tasa_retencion_honorarios"):
                # default seguro
                data["tasa_retencion_honorarios"] = 14.5
        return data 



class Paso5RepresentacionForm(forms.Form):
    rep_rut = forms.CharField(max_length=12, required=False, label="RUT representante legal")
    rep_nombre = forms.CharField(max_length=255, required=False, label="Nombre representante legal")

    def __init__(self, *args, **kwargs):
        self.tipo_actual = kwargs.pop("tipo_actual", None)
        super().__init__(*args, **kwargs)
        if self.tipo_actual == "PJ":
            self.fields["rep_rut"].required = True
            self.fields["rep_nombre"].required = True



class Paso6UsuarioAdminForm(forms.Form):
    email = forms.EmailField(label="Correo del administrador")
    password1 = forms.CharField(widget=forms.PasswordInput(), label="Contraseña")
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Confirmar contraseña")
    nombre = forms.CharField(max_length=150, label="Nombre")
    apellido = forms.CharField(max_length=150, required=False, label="Apellido")
    rut_personal = forms.CharField(max_length=12, label="RUT personal del administrador")

    def clean(self):
        data = super().clean()
        if data.get("password1") != data.get("password2"):
            self.add_error("password2", "Las contraseñas no coinciden.")
        if data.get("rut_personal"):
            rp = normalizar_rut(data["rut_personal"])
            validar_rut(rp)
            data["rut_personal"] = rp
        return data


class Paso7ConfirmacionForm(forms.Form):
    confirmar = forms.BooleanField(label="Confirmo que la información ingresada es correcta.")
