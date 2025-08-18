# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

Usuario = get_user_model()

def validar_rut_chileno(value: str):
    # MVP: valida patrón básico (más adelante implementamos dígito verificador real)
    import re
    if not re.match(r"^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$", value):
        raise forms.ValidationError("Formato de RUT inválido. Ej: 12.345.678-9")


class FormularioLogin(AuthenticationForm):
    # Mostramos "Email" en vez de "Usuario".
    # OJO: el campo sigue llamándose 'username' porque así lo espera AuthenticationForm.
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "placeholder": "tucorreo@dominio.cl"})
    )
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


class FormularioRegistroPersona(UserCreationForm):
    first_name = forms.CharField(label="Nombres", max_length=150)
    last_name  = forms.CharField(label="Apellidos", max_length=150)
    email      = forms.EmailField(label="Email")
    rut        = forms.CharField(label="RUT", validators=[validar_rut_chileno])
    telefono   = forms.CharField(label="Teléfono", required=False)

    class Meta:
        model = Usuario
        # NOTA: Eliminamos "username" del form público.
        fields = ("first_name", "last_name", "email", "rut", "telefono", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def clean_password1(self):
        pwd = self.cleaned_data.get("password1")
        validate_password(pwd)
        return pwd

    def save(self, commit=True):
        user = super().save(commit=False)
        # Usamos el email como username para simplificar login y compatibilidad
        email = self.cleaned_data["email"].strip().lower()
        user.username   = email
        user.email      = email
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name  = self.cleaned_data["last_name"].strip()
        user.rut        = self.cleaned_data["rut"].strip()
        # teléfono: si tu modelo de Usuario tiene campo, asigna; si no, omite
        if hasattr(user, "telefono"):
            user.telefono = self.cleaned_data.get("telefono", "").strip()
        if commit:
            user.save()
        return user


class FormularioRegistroEmpresa(UserCreationForm):
    # datos de usuario
    first_name = forms.CharField(label="Nombres", max_length=150)
    last_name  = forms.CharField(label="Apellidos", max_length=150)
    email      = forms.EmailField(label="Email")
    rut        = forms.CharField(label="RUT", validators=[validar_rut_chileno])
    telefono   = forms.CharField(label="Teléfono", required=False)

    # datos de empresa
    empresa_rut      = forms.CharField(label="RUT empresa", validators=[validar_rut_chileno])
    razon_social     = forms.CharField(label="Razón social")
    giro             = forms.CharField(required=False)
    regimen          = forms.ChoiceField(choices=[("pyme","Pro Pyme"),("general","Régimen general")], initial="pyme")
    direccion        = forms.CharField(required=False)
    comuna           = forms.CharField(required=False)
    region           = forms.CharField(required=False)
    contacto_email   = forms.EmailField(required=False)
    contacto_telefono= forms.CharField(required=False)

    class Meta:
        model = Usuario
        # NOTA: Eliminamos "username" del form público.
        fields = (
            "first_name", "last_name", "email", "rut", "telefono",
            "password1", "password2",
            "empresa_rut", "razon_social", "giro", "regimen",
            "direccion", "comuna", "region", "contacto_email", "contacto_telefono"
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def clean_password1(self):
        pwd = self.cleaned_data.get("password1")
        validate_password(pwd)
        return pwd

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"].strip().lower()
        user.username   = email
        user.email      = email
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name  = self.cleaned_data["last_name"].strip()
        user.rut        = self.cleaned_data["rut"].strip()
        if hasattr(user, "telefono"):
            user.telefono = self.cleaned_data.get("telefono", "").strip()
        if commit:
            user.save()
        return user
