from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
import json

# Imports movidos desde configuracion.py
from apps.integraciones.models import GoogleDriveCredential, DropboxCredential
from apps.empresas.models import Empresa 
from apps.panel.utils.empresa import get_empresa_activa

# --- NUEVOS IMPORTS PARA 2FA ---
import pyotp, secrets
# ---

def generate_recovery_codes(count=10):
    """Genera 10 códigos de recuperación únicos de 8 dígitos."""
    codes = []
    for _ in range(count):
        # Genera un número de 8 dígitos y lo formatea como cadena
        code = '{:08}'.format(secrets.randbelow(10**8))
        codes.append(code)
    return codes
# ---


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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # El contexto ya incluye 'user' (Modelo Usuario), que ahora tiene los campos 2FA
        ctx['user'] = self.request.user 
        return ctx

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # 1. Habilitar 2FA (redirige al setup)
        if 'action_enable_2fa' in request.POST:
            # Limpiamos el secreto antiguo de la sesión si existe
            if '2fa_secret' in request.session:
                del request.session['2fa_secret']
            return redirect(reverse("panel:ajustes_2fa_setup"))

        # 2. Deshabilitar 2FA
        elif 'action_disable_2fa' in request.POST:
            user.two_fa_enabled = False
            user.two_fa_secret = None 
            user.save()
            messages.success(request, "La autenticación de dos factores ha sido deshabilitada.")
            return redirect(reverse("panel:ajustes_privacidad"))
            
        # 3. Actualizar preferencias de privacidad (share_data)
        elif 'action_update_privacy' in request.POST:
            share_data = 'share_data' in request.POST
            
            user.share_data = share_data 
            user.save()
            
            messages.success(request, "Preferencias de privacidad guardadas.")
            return redirect(reverse("panel:ajustes_privacidad"))

        return redirect(reverse("panel:ajustes_privacidad"))


class Ajustes2FASetupView(LoginRequiredMixin, TemplateView): # <--- NUEVA CLASE
    """
    Muestra el código QR, almacena el secreto en sesión y verifica el código.
    """
    template_name = "panel/ajustes_2fa_setup.html"
    page_title = "Configurar 2FA"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Usamos la sesión para almacenar el secreto temporalmente
        secret = self.request.session.get('2fa_secret')

        if not secret:
            # Generar un nuevo secreto si no está en la sesión
            secret = pyotp.random_base32()
            self.request.session['2fa_secret'] = secret

        # Crea la URI para la app de autenticación
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="SGIDT" 
        )
        
        ctx['secret'] = secret
        ctx['totp_uri'] = totp_uri
        return ctx

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        code = request.POST.get('2fa_code', '').strip()
        secret = request.session.get('2fa_secret')
        user = request.user

        if not secret or not code:
            messages.error(request, "Error de sesión o código no proporcionado. Inténtalo de nuevo.")
            return redirect(reverse("panel:ajustes_privacidad"))

        totp = pyotp.TOTP(secret)

        if totp.verify(code):
            # Verificación exitosa: Guardar el secreto permanentemente y habilitar 2FA
            user.two_fa_secret = secret
            user.two_fa_enabled = True
            

            # --- NUEVO: Generar y guardar códigos de recuperación ---
            recovery_codes = generate_recovery_codes()
            user.two_fa_recovery_codes = recovery_codes
            # ------------------------------------------------------
            
            user.save()

            if '2fa_secret' in request.session:
                del request.session['2fa_secret'] # Limpiar secreto temporal
            
            messages.success(request, "¡Autenticación de dos factores habilitada correctamente!")
            return redirect(reverse("panel:ajustes_2fa_recovery"))
        else:
            messages.error(request, "Código de verificación inválido. Inténtalo de nuevo.")
            # Si la verificación falla, volvemos a mostrar el formulario.
            return self.get(request, *args, **kwargs)

# --- NUEVA VISTA PARA MOSTRAR/REGENERAR CÓDIGOS ---
class Ajustes2FARecoveryView(AjustesBase):
    """
    Muestra la lista de códigos de recuperación y maneja su regeneración.
    """
    template_name = "panel/ajustes_2fa_recovery.html"
    seccion = "privacidad"
    page_title = "Códigos de Recuperación 2FA"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.two_fa_enabled:
            messages.warning(self.request, "La autenticación de dos factores no está habilitada.")
            # Redirigir a privacidad si el 2FA no está activo
            return redirect(reverse("panel:ajustes_privacidad")) 

        ctx['recovery_codes'] = user.two_fa_recovery_codes
        return ctx
    
    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        user = request.user
        
        if 'action_regenerate_codes' in request.POST:
            # Regenerar códigos y guardar
            recovery_codes = generate_recovery_codes()
            user.two_fa_recovery_codes = recovery_codes
            user.save()
            
            messages.success(request, "Se han generado 10 nuevos códigos de recuperación. Los códigos anteriores han sido invalidados.")
            return redirect(reverse("panel:ajustes_2fa_recovery"))

        return redirect(reverse("panel:ajustes_2fa_recovery"))

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