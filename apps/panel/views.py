from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


from django.conf import settings
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .forms import HelpContactForm   
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.integraciones.models import GoogleDriveCredential, DropboxCredential

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.empresas.models import EmpresaUsuario

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "panel/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Si manejas empresa “activa” en sesión, respétala
        empresa_id = self.request.session.get("empresa_id")

        qs = (EmpresaUsuario.objects
              .select_related("empresa")
              .filter(usuario=self.request.user))  # Ojo: campo es `usuario`

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

class SettingsView(TemplateView):
    template_name = "panel/configuraciones.html"

class HelpView(TemplateView): 

    template_name = "panel/ayuda.html"



@require_POST
@csrf_protect
def help_contact(request):
    form = HelpContactForm(request.POST)

    # Helper: ¿es una petición AJAX?
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



#class SettingsView(LoginRequiredMixin, TemplateView):
#    template_name = "panel/configuraciones.html"

#    def get_context_data(self, **kwargs):
#        ctx = super().get_context_data(**kwargs)
#        ctx["drive_connected"] = GoogleDriveCredential.objects.filter(
#            user=self.request.user
#        ).exists()
#        return ctx
    

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "panel/configuraciones.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["drive_connected"]   = GoogleDriveCredential.objects.filter(user=u).exists()
        ctx["dropbox_connected"] = DropboxCredential.objects.filter(user=u).exists()
        return ctx