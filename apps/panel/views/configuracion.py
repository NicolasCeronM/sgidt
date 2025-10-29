# apps/panel/views/settings.py
from django.contrib import messages
from django.views.generic import TemplateView
from django.shortcuts import redirect, render
from django.conf import settings
from apps.integraciones.models import GoogleDriveCredential, DropboxCredential
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from apps.empresas.models import Empresa # Asegúrate que la importación es correcta
from apps.panel.utils.empresa import get_empresa_activa

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

# --- NUEVA VISTA PARA VERIFICAR ESTADO ---
@login_required
def check_email_sync_status(request):
    try:
        # Aquí pasamos el 'request' completo
        empresa = get_empresa_activa(request) 
        
        is_configured = False
        if empresa and empresa.email_host and empresa.email_user:
            is_configured = True
            
        return JsonResponse({"is_configured": is_configured})
        
    except Empresa.DoesNotExist:
        # Si el usuario no tiene empresa, no está configurado.
        return JsonResponse({"is_configured": False})
    except Exception as e:
        print(f"Error en check_email_sync_status: {e}")
        return JsonResponse({"is_configured": False, "error": "Error interno."})


@require_POST
@login_required
def save_email_sync_config(request):
    try:
        data = json.loads(request.body)
        
        # Aquí también pasamos el 'request' completo
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