# apps/usuarios/views.py
from __future__ import annotations
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from .forms import FormularioLogin



from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.views import LoginView
from .forms import FormularioLogin, UsuarioAdminConfigForm

from apps.empresas.forms import EmpresaAdminConfigForm
from apps.empresas.utils import get_empresa_activa, user_es_admin_de

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

class ConfiguracionAdministradorView(LoginRequiredMixin, View):
    template_name = "usuarios/config_admin.html"

    def get(self, request):
        empresa = get_empresa_activa(request)
        if not user_es_admin_de(request, empresa):
            return redirect("panel:dashboard")

        f_empresa = EmpresaAdminConfigForm(instance=empresa)
        f_usuario = UsuarioAdminConfigForm(instance=request.user)
        return render(request, self.template_name, {
            "empresa": empresa,
            "f_empresa": f_empresa,
            "f_usuario": f_usuario,
        })

    def post(self, request):
        empresa = get_empresa_activa(request)
        if not user_es_admin_de(request, empresa):
            return redirect("panel:dashboard")

        f_empresa = EmpresaAdminConfigForm(request.POST, request.FILES, instance=empresa)   # ← FILES
        f_usuario = UsuarioAdminConfigForm(request.POST, request.FILES, instance=request.user)  # ← FILES

        ok = True
        if "guardar_empresa" in request.POST:
            ok = f_empresa.is_valid()
            if ok:
                f_empresa.save()

        if "guardar_usuario" in request.POST:
            ok = f_usuario.is_valid() and ok
            if f_usuario.is_valid():
                f_usuario.save()

        if not ok:
            return render(request, self.template_name, {
                "empresa": empresa,
                "f_empresa": f_empresa,
                "f_usuario": f_usuario,
            })