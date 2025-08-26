# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class FormularioLogin(AuthenticationForm):
    username = forms.CharField(
        label="Correo o RUT",
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "placeholder": "tucorreo@dominio.cl o 12345678-9"
        })
    )
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

