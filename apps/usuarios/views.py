# apps/usuarios/views.py
from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.views import LoginView
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import (
    FormularioLogin,
    FormularioRegistroPersona,
    FormularioRegistroEmpresa,
)
from apps.empresas.models import Empresa

Usuario = get_user_model()

WELCOME_TEMPLATE_HTML = "correo/bienvenida.html"
WELCOME_TEMPLATE_TXT = "correo/bienvenida.txt"


def _send_welcome_email(user, request) -> None:
    """Envía el correo de bienvenida; no interrumpe el flujo si falla."""
    if not getattr(user, "email", None):
        return

    try:
        panel_url = request.build_absolute_uri(reverse("panel:dashboard"))
    except Exception:
        panel_url = request.build_absolute_uri("/app/")

    try:
        logo_url = request.build_absolute_uri(static("img/logo.png"))
    except Exception:
        logo_url = ""

    ctx = {"user": user, "panel_url": panel_url, "logo_url": logo_url, "now": timezone.now()}

    try:
        html = render_to_string(WELCOME_TEMPLATE_HTML, ctx)
        text = render_to_string(WELCOME_TEMPLATE_TXT, ctx)
        from_email = (
            getattr(settings, "DEFAULT_FROM_EMAIL", None)
            or getattr(settings, "EMAIL_HOST_USER", None)
            or "no-reply@localhost"
        )
        m = EmailMultiAlternatives("¡Bienvenido a SGIDT!", text, from_email, [user.email])
        m.attach_alternative(html, "text/html")
        m.send(fail_silently=False)
    except Exception:
        # Si quieres ver el error en consola mientras desarrollas, cambia a: raise
        pass


@require_http_methods(["GET", "POST"])
def registro_persona(request):
    if request.method == "POST":
        form = FormularioRegistroPersona(request.POST)
        if form.is_valid():
            with transaction.atomic():
                usuario: Usuario = form.save(commit=False)
                if hasattr(usuario, "tipo_contribuyente"):
                    usuario.tipo_contribuyente = "persona"
                usuario.save()

            _send_welcome_email(usuario, request)

            raw_password = form.cleaned_data.get("password1") or form.cleaned_data.get("password")
            user_auth = (
                authenticate(request, username=getattr(usuario, "email", ""), password=raw_password)
                or authenticate(request, username=usuario.username, password=raw_password)
            )
            if user_auth:
                login(request, user_auth)

            messages.success(request, "Tu cuenta fue creada con éxito. ¡Bienvenido!")
            return redirect(reverse("panel:dashboard"))
    else:
        form = FormularioRegistroPersona()

    return render(request, "usuarios/registro_persona.html", {"form": form})


@require_http_methods(["GET", "POST"])
def registro_empresa(request):
    if request.method == "POST":
        form = FormularioRegistroEmpresa(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1) Usuario
                    usuario: Usuario = form.save(commit=False)
                    if hasattr(usuario, "tipo_contribuyente"):
                        usuario.tipo_contribuyente = "empresa"
                    usuario.save()

                    # 2) Empresa asociada
                    Empresa.objects.create(
                        rut=form.cleaned_data["empresa_rut"],
                        razon_social=form.cleaned_data["razon_social"],
                        giro=form.cleaned_data.get("giro", ""),
                        regimen=form.cleaned_data.get("regimen", "pyme"),
                        direccion=form.cleaned_data.get("direccion", ""),
                        comuna=form.cleaned_data.get("comuna", ""),
                        region=form.cleaned_data.get("region", ""),
                        contacto_email=form.cleaned_data.get("contacto_email", ""),
                        contacto_telefono=form.cleaned_data.get("contacto_telefono", ""),
                        propietario=usuario,
                    )
            except IntegrityError:
                form.add_error("empresa_rut", "Ya existe una empresa registrada con este RUT.")
            else:
                _send_welcome_email(usuario, request)

                raw_password = form.cleaned_data.get("password1") or form.cleaned_data.get("password")
                user_auth = (
                    authenticate(request, username=getattr(usuario, "email", ""), password=raw_password)
                    or authenticate(request, username=usuario.username, password=raw_password)
                )
                if user_auth:
                    login(request, user_auth)

                messages.success(request, "Empresa y cuenta creadas correctamente. ¡Bienvenido!")
                return redirect(reverse("panel:dashboard"))
    else:
        form = FormularioRegistroEmpresa()

    return render(request, "usuarios/registro_empresa.html", {"form": form})


class VistaLogin(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = FormularioLogin
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("panel:dashboard")


def cerrar_sesion(request):
    logout(request)
    return redirect("usuarios:login")
