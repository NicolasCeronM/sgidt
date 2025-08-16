# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from .models import Usuario

def validar_rut_chileno(value: str):
    # MVP: valida patrón básico (más adelante implementamos dígito verificador real)
    import re
    if not re.match(r"^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$", value):
        raise forms.ValidationError("Formato de RUT inválido. Ej: 12.345.678-9")

class FormularioLogin(AuthenticationForm):
    username = forms.CharField(label="Usuario")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

class FormularioRegistroPersona(UserCreationForm):
    rut = forms.CharField(validators=[validar_rut_chileno])
    telefono = forms.CharField(required=False)

    class Meta:
        model = Usuario
        fields = ("username", "email", "rut", "telefono", "password1", "password2")

    def clean_password1(self):
        pwd = self.cleaned_data.get("password1")
        validate_password(pwd)
        return pwd

class FormularioRegistroEmpresa(UserCreationForm):
    # datos de usuario
    rut = forms.CharField(validators=[validar_rut_chileno])
    telefono = forms.CharField(required=False)
    # datos de empresa
    empresa_rut = forms.CharField(label="RUT empresa", validators=[validar_rut_chileno])
    razon_social = forms.CharField()
    giro = forms.CharField(required=False)
    regimen = forms.ChoiceField(choices=[("pyme","Pro Pyme"),("general","Régimen general")], initial="pyme")
    direccion = forms.CharField(required=False)
    comuna = forms.CharField(required=False)
    region = forms.CharField(required=False)
    contacto_email = forms.EmailField(required=False)
    contacto_telefono = forms.CharField(required=False)

    class Meta:
        model = Usuario
        fields = ("username", "email", "rut", "telefono", "password1", "password2")
