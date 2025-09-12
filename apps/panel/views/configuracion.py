# apps/panel/views/settings.py
from django.contrib import messages
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.conf import settings
from apps.integraciones.models import GoogleDriveCredential, DropboxCredential

class SettingsView(TemplateView):
    template_name = "panel/configuraciones.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["drive_connected"] = GoogleDriveCredential.objects.filter(user=u).exists()
        ctx["dropbox_connected"] = DropboxCredential.objects.filter(user=u).exists()
        return ctx

    def post(self, request, *args, **kwargs):
        # TODO: persistir datos reales de empresa si corresponde
        company_rut = request.POST.get("company_rut", "").strip()
        company_name = request.POST.get("company_name", "").strip()

        if not company_rut or not company_name:
            messages.error(request, "RUT y Razón Social son obligatorios.")
            return redirect("panel:configuraciones")

        messages.success(request, "Configuración guardada con éxito.")
        return redirect("panel:configuraciones")
