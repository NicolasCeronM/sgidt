# usuarios/views.py
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .forms import (
    FormularioLogin, FormularioRegistroPersona, FormularioRegistroEmpresa
)
from .models import Usuario
from apps.empresas.models import Empresa
from django.urls import reverse_lazy


class VistaLogin(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = FormularioLogin
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("panel:dashboard")

@require_http_methods(["GET","POST"])
def registro_persona(request):
    if request.method == "POST":
        form = FormularioRegistroPersona(request.POST)
        if form.is_valid():
            usuario: Usuario = form.save(commit=False)
            usuario.tipo_contribuyente = "persona"
            usuario.save()
            login(request, usuario)
            return redirect(reverse("pages:home"))
    else:
        form = FormularioRegistroPersona()
    return render(request, "usuarios/registro_persona.html", {"form": form})

@require_http_methods(["GET","POST"])
def registro_empresa(request):
    if request.method == "POST":
        form = FormularioRegistroEmpresa(request.POST)
        if form.is_valid():
            # 1) crear usuario
            usuario: Usuario = form.save(commit=False)
            usuario.tipo_contribuyente = "empresa"
            usuario.save()
            # 2) crear empresa asociada
            empresa = Empresa.objects.create(
                rut=form.cleaned_data["empresa_rut"],
                razon_social=form.cleaned_data["razon_social"],
                giro=form.cleaned_data.get("giro",""),
                regimen=form.cleaned_data.get("regimen","pyme"),
                direccion=form.cleaned_data.get("direccion",""),
                comuna=form.cleaned_data.get("comuna",""),
                region=form.cleaned_data.get("region",""),
                contacto_email=form.cleaned_data.get("contacto_email",""),
                contacto_telefono=form.cleaned_data.get("contacto_telefono",""),
                propietario=usuario,
            )
            login(request, usuario)
            return redirect(reverse("home"))
    else:
        form = FormularioRegistroEmpresa()
    return render(request, "usuarios/registro_empresa.html", {"form": form})

def cerrar_sesion(request):
    logout(request)
    return redirect("usuarios:login")
