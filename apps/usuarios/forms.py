# usuarios/forms.py
from __future__ import annotations
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator

Usuario = get_user_model()

#
class FormularioLogin(AuthenticationForm):
    username = forms.CharField(
        label="Correo o RUT",
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "placeholder": "tucorreo@dominio.cl o 12345678-9"
        })
    )
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


# Formulario para solicitar restablecimiento de contraseña
User = get_user_model()

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@dominio.cl"})
    )

class PasswordResetVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    code = forms.CharField(
        label="Código de verificación",
        max_length=6,
        widget=forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric", "autocomplete": "one-time-code", "placeholder": "6 dígitos"})
    )

class PasswordResetSetForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    code = forms.CharField(widget=forms.HiddenInput())
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"})
    )
    password2 = forms.CharField(
        label="Repite la contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"})
    )

    def clean(self):
        data = super().clean()
        if data.get("password1") != data.get("password2"):
            raise forms.ValidationError("Las contraseñas no coinciden.")
        if data.get("password1") and len(data["password1"]) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return data

class UsuarioAdminConfigForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "email", "telefono", "comuna", "region", "foto"]
        widgets = {
            "email": forms.EmailInput(attrs={"readonly": "readonly"}),
        }