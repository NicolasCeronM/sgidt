from __future__ import annotations
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Empresa, EmpresaUsuario, RegimenTributario, TipoSocietario, normalizar_rut, validar_rut

User = get_user_model()

class RegistroPyMEForm(forms.Form):
    # --- Empresa ---
    empresa_rut = forms.CharField(label="RUT de la empresa", max_length=12)
    razon_social = forms.CharField(label="Nombre o razón social", max_length=255)
    tipo_societario = forms.ChoiceField(label="Tipo societario", choices=TipoSocietario.choices, initial=TipoSocietario.SPA)
    regimen_tributario = forms.ChoiceField(label="Régimen tributario", choices=RegimenTributario.choices, initial=RegimenTributario.PYME_GENERAL)
    giro = forms.CharField(label="Giro (opcional)", max_length=255, required=False)
    codigo_actividad = forms.CharField(label="Código actividad SII (opcional)", max_length=6, required=False)
    email_empresa = forms.EmailField(label="Email empresa (opcional)", required=False)
    telefono = forms.CharField(label="Teléfono (opcional)", max_length=20, required=False)
    direccion = forms.CharField(label="Dirección (opcional)", max_length=255, required=False)
    comuna = forms.CharField(label="Comuna (opcional)", max_length=80, required=False)
    region = forms.CharField(label="Región (opcional)", max_length=80, required=False)

    # --- Usuario admin ---
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    user_email = forms.EmailField(label="Email de acceso")
    user_rut = forms.CharField(label="RUT del representante (opcional)", max_length=12, required=False)
    password1 = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repite la contraseña", strip=False, widget=forms.PasswordInput)
    aceptar_terminos = forms.BooleanField(label="Acepto términos y condiciones", required=True)

    # ---------- Validaciones ----------
    def clean_empresa_rut(self):
        rut = normalizar_rut(self.cleaned_data["empresa_rut"])
        validar_rut(rut)
        if Empresa.objects.filter(rut=rut).exists():
            raise ValidationError("Ya existe una empresa con este RUT.")
        return rut

    def clean_user_rut(self):
        rut = (self.cleaned_data.get("user_rut") or "").strip()
        if not rut:
            return ""
        rut = normalizar_rut(rut)
        validar_rut(rut)
        # Si tu User tiene rut único:
        if hasattr(User, "rut") and User.objects.filter(rut=rut).exists():
            raise ValidationError("Ya existe un usuario con este RUT.")
        return rut

    def clean_user_email(self):
        email = self.cleaned_data["user_email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario con este email.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    # ---------- Persistencia ----------
    def save(self, *, commit=True) -> tuple[Empresa, User, EmpresaUsuario]:
        data = self.cleaned_data

        empresa = Empresa(
            rut=data["empresa_rut"],
            razon_social=data["razon_social"],
            tipo_societario=data["tipo_societario"],
            regimen_tributario=data["regimen_tributario"],
            giro=data.get("giro") or "",
            codigo_actividad=data.get("codigo_actividad") or "",
            email=data.get("email_empresa") or "",
            telefono=data.get("telefono") or "",
            direccion=data.get("direccion") or "",
            comuna=data.get("comuna") or "",
            region=data.get("region") or "",
        )
        empresa.full_clean()
        if commit:
            empresa.save()

        # Crea usuario admin
        user_kwargs = dict(
            email=data["user_email"].lower().strip(),
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
            is_active=True,
        )
        # Solo setea rut si tu modelo User lo tiene
        if hasattr(User, "rut"):
            user_kwargs["rut"] = data.get("user_rut") or None

        user = User.objects.create_user(
        username=data["user_email"],  # 👈 porque AbstractUser lo pide
        email=data["user_email"].lower().strip(),
        password=data["password1"],
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        rut=data.get("user_rut") or None,
        tipo_contribuyente="empresa",
        )   


        membership = EmpresaUsuario(usuario=user, empresa=empresa, rol="admin")
        if commit:
            membership.save()

        return empresa, user, membership

    # ---------- Estilos (opcional) ----------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegura choices por si algo los sobreescribe
        self.fields["tipo_societario"].choices = list(TipoSocietario.choices)
        self.fields["regimen_tributario"].choices = list(RegimenTributario.choices)
        # Bootstrap-look rápido
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "form-select"})
            else:
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (css + " form-control").strip()
