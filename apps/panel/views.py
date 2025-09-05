from urllib import request
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from apps.integraciones.models import GoogleDriveCredential, DropboxCredential
from apps.empresas.models import EmpresaUsuario

# PDF
from weasyprint import HTML, CSS
import os

from .forms import HelpContactForm


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "panel/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Si manejas empresa “activa” en sesión, respétala
        empresa_id = self.request.session.get("empresa_id")

        qs = (
            EmpresaUsuario.objects
            .select_related("empresa")
            .filter(usuario=self.request.user)  # Ojo: campo es `usuario`
        )

        if empresa_id:
            eu = qs.filter(empresa_id=empresa_id).first()
        else:
            eu = qs.order_by("creado_en").first()

        ctx["empresa"] = eu.empresa if eu else None
        return ctx


class DocsView(TemplateView):
    template_name = "panel/documentos.html"


class ReportsView(TemplateView):
    template_name = "panel/reportes.html"


class ValidationsView(TemplateView):
    template_name = "panel/validaciones.html"


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "panel/configuraciones.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["drive_connected"] = GoogleDriveCredential.objects.filter(user=u).exists()
        ctx["dropbox_connected"] = DropboxCredential.objects.filter(user=u).exists()
        return ctx

    def post(self, request, *args, **kwargs):
        """
        Maneja el submit de 'Ajustes de la Empresa'.
        Por ahora solo muestra feedback y redirige (PRG pattern).
        Si luego agregamos persistencia, aquí haremos form.is_valid() -> form.save().
        """
        company_rut = request.POST.get("company_rut", "").strip()
        company_name = request.POST.get("company_name", "").strip()
        company_email = request.POST.get("company_email", "").strip()
        company_phone = request.POST.get("company_phone", "").strip()
        company_addr = request.POST.get("company_address", "").strip()
        auto_backup = request.POST.get("auto_backup", "").strip()  # si lo usas

        # Validación mínima (opcional, puedes ajustar)
        if not company_rut or not company_name:
            messages.error(request, "RUT y Razón Social son obligatorios.")
            return redirect("panel:configuraciones")

        # TODO: persistir en BD (CompanySettings / Empresa). Por ahora, solo feedback.
        messages.success(request, "Configuración guardada con éxito.")
        return redirect("panel:configuraciones")


class HelpView(TemplateView):
    template_name = "panel/ayuda.html"


class FAQView(LoginRequiredMixin, TemplateView):
    template_name = "panel/faq.html"


class StatusView(LoginRequiredMixin, TemplateView):
    template_name = "panel/estado.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Placeholder: lista de servicios con estados simulados
        ctx["services"] = [
            {"name": "API SGIDT", "status": "operational", "note": "Sin incidentes"},
            {"name": "Google Drive", "status": "degraded", "note": "Latencias intermitentes"},
            {"name": "Dropbox", "status": "operational", "note": "OK"},
            {"name": "Correo saliente", "status": "maintenance", "note": "Ventana 00:30–01:00"},
        ]
        ctx["last_updated"] = "Actualizado hace 2 min (placeholder)"
        return ctx


@require_POST
@csrf_protect
def help_contact(request):
    form = HelpContactForm(request.POST)

    # ¿Es una petición AJAX?
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    # Validación
    if not form.is_valid():
        if is_ajax:
            # Devolvemos errores de forma segura para el fetch()
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        messages.error(request, "Revisa los campos del formulario.")
        return redirect(reverse("panel:ayuda"))

    # Datos
    name = form.cleaned_data["name"]
    email = form.cleaned_data["email"]
    message = form.cleaned_data["message"]

    # Render de plantillas de correo
    context = {"name": name, "email": email, "message": message}
    text_content = render_to_string("correo/ayuda_contacto.txt", context)
    html_content = render_to_string("correo/ayuda_contacto.html", context)

    # Envío
    subject = f"[SGIDT] Contacto de ayuda - {name}"
    to = [getattr(settings, "SUPPORT_EMAIL", "sgidtchile@gmail.com")]

    email_msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=to,
        reply_to=[email],
    )
    email_msg.attach_alternative(html_content, "text/html")
    email_msg.send()

    # Éxito → si es AJAX devolvemos JSON, si no usamos messages + redirect
    if is_ajax:
        return JsonResponse({"ok": True})

    messages.success(request, "Tu mensaje fue enviado. Te contactaremos pronto.")
    return redirect(reverse("panel:ayuda"))


# ===========================
#   PDF: Manual de Usuario
# ===========================
def manual_usuario_pdf(request):
    """
    Genera y descarga el Manual de Usuario en PDF
    a partir de la plantilla templates/manual/manual_usuario.html
    y el CSS de impresión en static/manual/css/manual_print.css
    """
    secciones = [
        {
            "id": "introduccion",
            "titulo": "Introducción",
            "html": """
                <p><strong>SGIDT</strong> es un sistema de gestión inteligente tributario para pymes chilenas.
                Este manual explica la navegación, los módulos y ejemplos de uso paso a paso.</p>
            """,
        },
        {
            "id": "cuentas",
            "titulo": "Cuentas de Usuario y Acceso",
            "html": """
                <ul>
                    <li>Registro, inicio de sesión y recuperación de contraseña.</li>
                    <li>Gestión de perfil y permisos.</li>
                </ul>
            """,
        },
        {
            "id": "validaciones",
            "titulo": "Validaciones con SII (SimpleAPI)",
            "html": """
                <p>Cómo subir XML/JSON de DTE, lanzar la validación y leer los resultados.
                Recomendaciones para errores frecuentes.</p>
            """,
        },
        {
            "id": "integraciones",
            "titulo": "Integraciones: Google Drive y Dropbox",
            "html": """
                <p>Conectar cuentas, otorgar permisos, persistencia de tokens y explorar/descargar archivos.</p>
            """,
        },
        {
            "id": "panel_estado",
            "titulo": "Centro de Estado",
            "html": """
                <p>Monitoreo de servicios, integraciones y disponibilidad del sistema.</p>
            """,
        },
        {
            "id": "soporte",
            "titulo": "Soporte y Contacto",
            "html": """
                <p>Flujo para reportar incidencias desde Ayuda → Contacto Rápido y buenas prácticas.</p>
            """,
        },
    ]

    context = {
        "titulo": "SGIDT · Manual de Usuario",
        "version": "v1.0",
        "empresa": "SGIDT",
        "secciones": secciones,
    }

    html_string = render_to_string("manual/manual_usuario.html", context)

    css_fs = os.path.join(settings.BASE_DIR, "static", "manual", "css", "manual_print.css")
    stylesheets = [CSS(filename=css_fs)] if os.path.exists(css_fs) else []

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(
        stylesheets=stylesheets
    )

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="sgidt-manual.pdf"'
    return response
