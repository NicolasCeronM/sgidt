# apps/panel/views.py
from typing import Any, Dict
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView, FormView

from apps.empresas.models import EmpresaUsuario
from apps.integraciones.models import GoogleDriveCredential, DropboxCredential
from .forms import HelpContactForm


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _is_ajax(request: HttpRequest) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _empresa_activa_para(request: HttpRequest):
    """
    Devuelve la Empresa activa del usuario, respetando la sesión.
    Unifica el uso a 'empresa_activa_id' en todo el proyecto.
    """
    empresa_id = request.session.get("empresa_activa_id")
    qs = (EmpresaUsuario.objects
          .select_related("empresa")
          .filter(usuario=request.user))

    if empresa_id:
        eu = qs.filter(empresa_id=empresa_id).first()
        if eu:
            return eu.empresa
    # fallback primera empresa del usuario
    eu = qs.order_by("creado_en").first()
    return eu.empresa if eu else None


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "panel/dashboard.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["empresa"] = _empresa_activa_para(self.request)
        return ctx


# ---------------------------------------------------------------------
# Documentos (Front: sólo renderiza template; el JS llama a /api/documentos/..)
# ---------------------------------------------------------------------
class DocumentosPageView(LoginRequiredMixin, TemplateView):
    template_name = "panel/documentos.html"


# ---------------------------------------------------------------------
# Reportes / Validaciones / Ayuda / FAQ / Estado
# ---------------------------------------------------------------------
class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "panel/reportes.html"


class ValidationsView(LoginRequiredMixin, TemplateView):
    template_name = "panel/validaciones.html"


class HelpView(LoginRequiredMixin, TemplateView):
    template_name = "panel/ayuda.html"


class FAQView(LoginRequiredMixin, TemplateView):
    template_name = "panel/faq.html"


class StatusView(LoginRequiredMixin, TemplateView):
    template_name = "panel/estado.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        # Placeholder: puedes reemplazar por un healthcheck real
        ctx["services"] = [
            {"name": "API SGIDT", "status": "operational", "note": "Sin incidentes"},
            {"name": "Google Drive", "status": "degraded", "note": "Latencias intermitentes"},
            {"name": "Dropbox", "status": "operational", "note": "OK"},
            {"name": "Correo saliente", "status": "maintenance", "note": "Ventana 00:30–01:00"},
        ]
        ctx["last_updated"] = "Actualizado hace 2 min (placeholder)"
        return ctx


# ---------------------------------------------------------------------
# Help Contact (Form + JSON si es AJAX)  —> ideal para delegar a Celery luego
# ---------------------------------------------------------------------
class HelpContactView(LoginRequiredMixin, FormView):
    template_name = "panel/ayuda.html"
    form_class = HelpContactForm
    success_url = reverse_lazy("panel:ayuda")

    def form_invalid(self, form):
        if _is_ajax(self.request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        messages.error(self.request, "Revisa los campos del formulario.")
        return super().form_invalid(form)

    def form_valid(self, form):
        name = form.cleaned_data["name"]
        email = form.cleaned_data["email"]
        message = form.cleaned_data["message"]

        context = {"name": name, "email": email, "message": message}
        text_content = render_to_string("correo/ayuda_contacto.txt", context)
        html_content = render_to_string("correo/ayuda_contacto.html", context)

        subject = f"[SGIDT] Contacto de ayuda - {name}"
        to = [getattr(settings, "SUPPORT_EMAIL", "sgidtchile@gmail.com")]
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

        # Envío sin Celery (por ahora). Luego puedes delegar a tasks.email_send.delay(...)
        from django.core.mail import EmailMultiAlternatives
        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to,
            reply_to=[email],
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()

        if _is_ajax(self.request):
            return JsonResponse({"ok": True})

        messages.success(self.request, "Tu mensaje fue enviado. Te contactaremos pronto.")
        return super().form_valid(form)


# ---------------------------------------------------------------------
# Configuraciones
# ---------------------------------------------------------------------
class SettingsView(LoginRequiredMixin, TemplateView):
    """
    Vista de configuración del panel. Muestra estado de integraciones y
    recibe datos básicos de la empresa (PRG pattern).
    """
    template_name = "panel/configuraciones.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["drive_connected"] = GoogleDriveCredential.objects.filter(user=u).exists()
        ctx["dropbox_connected"] = DropboxCredential.objects.filter(user=u).exists()
        ctx["empresa"] = _empresa_activa_para(self.request)
        return ctx

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Maneja el submit de 'Ajustes de la Empresa'.
        Mantiene PRG y validación mínima. A futuro, persistir en Empresa/CompanySettings.
        """
        company_rut   = (request.POST.get("company_rut") or "").strip()
        company_name  = (request.POST.get("company_name") or "").strip()
        company_email = (request.POST.get("company_email") or "").strip()
        company_phone = (request.POST.get("company_phone") or "").strip()
        company_addr  = (request.POST.get("company_address") or "").strip()
        auto_backup   = (request.POST.get("auto_backup") or "").strip()

        if not company_rut or not company_name:
            messages.error(request, "RUT y Razón Social son obligatorios.")
            return redirect("panel:configuraciones")

        # TODO: persistir datos en la empresa activa o en un modelo de settings.
        messages.success(request, "Configuración guardada con éxito.")
        return redirect("panel:configuraciones")
