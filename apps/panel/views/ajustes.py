from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

# Imports desde otras apps
from apps.integraciones.models import GoogleDriveCredential, DropboxCredential
from apps.empresas.models import Empresa
from apps.panel.utils.empresa import get_empresa_activa


# ============================================================
#                     BASE DE AJUSTES
# ============================================================

class AjustesBase(LoginRequiredMixin, TemplateView):
    template_name = "panel/ajustes.html"
    seccion = "general"
    page_title = "Ajustes"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["seccion"] = self.seccion
        ctx["page_title"] = self.page_title
        return ctx


# ============================================================
#                     AJUSTES GENERALES
# ============================================================

class AjustesGeneralView(AjustesBase):
    seccion = "general"
    page_title = "Ajustes generales"

    def post(self, request, *args, **kwargs):
        """
        Maneja los formularios de Apariencia, Localización y Localizar.
        """

        # --- FORMULARIO DE APARIENCIA ---
        if 'action_update_appearance' in request.POST:
            theme = request.POST.get('theme', 'system')
            tips_enabled = 'tips' in request.POST

            # Guardar preferencias en el perfil del usuario o sesión
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                profile.theme = theme
                profile.show_tips = tips_enabled
                profile.save()
                messages.success(request, "Apariencia actualizada correctamente.")
            else:
                request.session['theme'] = theme
                request.session['show_tips'] = tips_enabled
                messages.success(request, "Apariencia guardada temporalmente en la sesión.")

            return redirect('panel:ajustes_general')

        # --- FORMULARIO DE LOCALIZACIÓN ---
        elif 'action_update_locale' in request.POST:
            lang = request.POST.get('lang', 'es')
            tz = request.POST.get('tz', 'UTC')
            date_format = request.POST.get('date_format', 'dd/mm/aaaa')
            number_format = request.POST.get('number_format', '.,')

            # Guardar preferencias
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                profile.language = lang
                profile.timezone = tz
                profile.date_format = date_format
                profile.number_format = number_format
                profile.save()
                messages.success(request, "Preferencias de localización guardadas correctamente.")
            else:
                request.session['lang'] = lang
                request.session['tz'] = tz
                request.session['date_format'] = date_format
                request.session['number_format'] = number_format
                messages.success(request, "Preferencias guardadas temporalmente en la sesión.")

            return redirect('panel:ajustes_general')

        # --- BOTÓN DE LOCALIZAR (APLICAR SIN GUARDAR) ---
        elif 'action_apply_locale' in request.POST:
            lang = request.POST.get('lang', 'es')
            tz = request.POST.get('tz', 'UTC')

            from django.utils import translation, timezone
            import pytz

            request.session['django_language'] = lang
            request.session['user_timezone'] = tz

            translation.activate(lang)
            try:
                timezone.activate(pytz.timezone(tz))
            except pytz.UnknownTimeZoneError:
                timezone.deactivate()

            messages.success(request, f"Idioma '{lang}' y zona horaria '{tz}' aplicados temporalmente.")
            return redirect('panel:ajustes_general')

        # --- POST sin acción reconocida ---
        messages.error(request, "No se reconoció la acción del formulario.")
        return redirect('panel:ajustes_general')


# ============================================================
#                     AJUSTES DE CUENTA (PERFIL)
# ============================================================

class AjustesCuentaView(AjustesBase):
    seccion = "cuenta"
    page_title = "Cuenta de usuario"

    def post(self, request, *args, **kwargs):
        """
        Maneja el formulario de 'Actualizar perfil'.
        """
        if 'action_update_profile' in request.POST:
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()

            user = request.user
            try:
                # Actualizar datos básicos del usuario
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.save()

                # Si existe perfil, actualizarlo también
                if hasattr(user, 'profile'):
                    profile = user.profile
                    profile.phone = request.POST.get('phone', '').strip()
                    profile.position = request.POST.get('position', '').strip()
                    profile.save()

                messages.success(request, "Perfil actualizado correctamente.")
                return redirect('panel:ajustes_cuenta')

            except Exception as e:
                messages.error(request, f"Ocurrió un error al actualizar el perfil: {e}")
                return redirect('panel:ajustes_cuenta')

        messages.error(request, "No se reconoció la acción del formulario.")
        return redirect('panel:ajustes_cuenta')


# ============================================================
#                     OTRAS SECCIONES
# ============================================================

class AjustesPrivacidadView(AjustesBase):
    seccion = "privacidad"


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
        company_rut = request.POST.get("company_rut", "").strip()
        company_name = request.POST.get("company_name", "").strip()

        if not company_rut or not company_name:
            messages.error(request, "RUT y Razón Social son obligatorios.")
            return redirect("panel:ajustes_empresa")

        try:
            empresa = get_empresa_activa(request)
            if empresa:
                empresa.rut = company_rut
                empresa.razon_social = company_name
                empresa.save()
                messages.success(request, "Datos de la empresa actualizados correctamente.")
            else:
                messages.error(request, "No se encontró una empresa activa.")
        except Empresa.DoesNotExist:
            messages.error(request, "No se encontró una empresa activa.")
        except Exception as e:
            messages.error(request, f"Error al guardar la empresa: {e}")

        return redirect("panel:ajustes_empresa")


# ============================================================
#                     LANDING DE AJUSTES
# ============================================================

def ajustes_landing(request):
    return redirect(reverse("panel:ajustes_general"))


# ============================================================
#                     API AUXILIAR
# ============================================================

@login_required
def check_email_sync_status(request):
    try:
        empresa = get_empresa_activa(request)
        is_configured = bool(empresa and empresa.email_host and empresa.email_user)
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
        return JsonResponse({"status": "error", "message": "No se encontró una empresa activa."}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Datos inválidos."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


