from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

# Imports movidos desde configuracion.py
from apps.integraciones.models import GoogleDriveCredential, DropboxCredential
from apps.empresas.models import Empresa 
from apps.panel.utils.empresa import get_empresa_activa


class AjustesBase(LoginRequiredMixin, TemplateView):
    template_name = "panel/ajustes.html"
    seccion = "general"
    page_title = "Ajustes"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["seccion"] = self.seccion
        ctx["page_title"] = self.page_title
        return ctx

class AjustesGeneralView(AjustesBase):
    seccion = "general"

class AjustesCuentaView(AjustesBase):
    seccion = "cuenta"

class AjustesPrivacidadView(AjustesBase):
    seccion = "privacidad"

# --- Vistas movidas desde configuracion.py ---

class AjustesIntegracionesView(AjustesBase):
    seccion = "integraciones"
    page_title = "Integraciones"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["drive_connected"] = GoogleDriveCredential.objects.filter(user=u).exists()
        ctx["dropbox_connected"] = DropboxCredential.objects.filter(user=u).exists()
        return ctx

class AjustesEmpresaView(AjustesBase):
    seccion = "empresa"
    page_title = "Datos de la Empresa"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            empresa = get_empresa_activa(self.request)
            ctx["empresa"] = empresa
        except Empresa.DoesNotExist:
            ctx["empresa"] = None
        return ctx

    def post(self, request, *args, **kwargs):
        # Lógica del POST que estaba en configuracion.py
        company_rut = request.POST.get("company_rut", "").strip()
        company_name = request.POST.get("company_name", "").strip()

        if not company_rut or not company_name:
            messages.error(request, "RUT y Razón Social son obligatorios.")
            return redirect("panel:ajustes_empresa")

        try:
            empresa = get_empresa_activa(request)
            if empresa:
                # Asumiendo que los campos del modelo se llaman 'rut' y 'razon_social'
                empresa.rut = company_rut 
                empresa.razon_social = company_name 
                # ... guardar otros campos del formulario ...
                empresa.save()
                messages.success(request, "Datos de la empresa actualizados.")
            else:
                messages.error(request, "No se encontró una empresa activa.")
        except Empresa.DoesNotExist:
             messages.error(request, "No se encontró una empresa activa.")
        except Exception as e:
             messages.error(request, f"Error al guardar la empresa: {e}")

        return redirect("panel:ajustes_empresa")


def ajustes_landing(request):
    return redirect(reverse("panel:ajustes_general"))


# --- Vistas API movidas desde configuracion.py ---

@login_required
def check_email_sync_status(request):
    try:
        empresa = get_empresa_activa(request) 
        
        is_configured = False
        if empresa and empresa.email_host and empresa.email_user:
            is_configured = True
            
        return JsonResponse({"is_configured": is_configured})
        
    except Empresa.DoesNotExist:
        return JsonResponse({"is_configured": False})
    except Exception as e:
        print(f"Error en check_email_sync_status: {e}")
        return JsonResponse({"is_configured": False, "error": "Error interno."})


@require_POST
@login_required
def save_email_sync_config(request):
    try:
        data = json.loads(request.body)
        empresa = get_empresa_activa(request)
        
        if not empresa:
            return JsonResponse({"status": "error", "message": "No se encontró una empresa activa."}, status=400)

        email_user = data.get('email_user')
        email_password = data.get('password')
        provider = data.get('provider')

        if not all([email_user, email_password, provider]):
            return JsonResponse({"status": "error", "message": "Todos los campos son requeridos."}, status=400)

        if provider == 'gmail':
            empresa.email_host = 'imap.gmail.com'
            empresa.email_port = 993
        elif provider == 'outlook':
            empresa.email_host = 'outlook.office365.com'
            empresa.email_port = 993
        else:
            return JsonResponse({"status": "error", "message": "Proveedor de correo no válido."}, status=400)

        empresa.email_user = email_user
        empresa.email_password = email_password
        empresa.email_use_ssl = True
        
        empresa.save()

        return JsonResponse({"status": "success", "message": "¡Configuración guardada correctamente!"})

    except Empresa.DoesNotExist:
        return JsonResponse({"status": "error", "message": "No se encontró una empresa activa para guardar."}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Datos inválidos."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)