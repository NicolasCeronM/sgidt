# apps/usuarios/views.py
from __future__ import annotations
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .forms import FormularioLogin

Usuario = get_user_model()


class VistaLogin(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = FormularioLogin
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("panel:dashboard")


def cerrar_sesion(request):
    logout(request)
    return redirect("usuarios:login")
