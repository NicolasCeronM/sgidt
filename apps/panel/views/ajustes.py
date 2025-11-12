from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
import json, pyotp, secrets, os

# --- Imports desde otras apps ---
from apps.integraciones.models import GoogleDriveCredential, DropboxCredential
from apps.empresas.models import Empresa
from apps.panel.utils.empresa import get_empresa_activa


# ------------------------------
# FUNCIONES AUXILIARES
# ------------------------------

def generate_recovery_codes(count=10):
    """Genera 10 códigos de recuperación únicos de 8 dígitos."""
    return ['{:08}'.format(secrets.randbelow(10**8)) for _ in range(count)]


def handle_uploaded_file(file, folder, prefix):
    """Guarda archivos subidos (como logos o avatares) en MEDIA_ROOT."""
    if not file:
        return None

    if file.size > 2 * 1024 * 1024:
        raise ValueError("El archivo no debe superar los 2 MB.")

    if file.content_type not in ['image/jpeg', 'image/png']:
        raise ValueError("Formato no válido. Usa JPG o PNG.")

    upload_dir = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"{prefix}_{secrets.token_hex(4)}{os.path.splitext(file.name)[1]}"
    path = os.path.join(upload_dir, filename)

    with open(path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return f"{folder}/{filename}"


# ------------------------------
# CLASE BASE
# ------------------------------

class AjustesBase(LoginRequiredMixin, TemplateView):
    template_name = "panel/ajustes.html"
    seccion = "general"
    page_title = "Ajustes"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["seccion"] = self.seccion
        ctx["page_title"] = self.page_title
        return ctx


# ------------------------------
# APARIENCIA Y LOCALIZACIÓN
# ------------------------------

class AjustesGeneralView(AjustesBase):
    seccion = "general"
    page_title = "Ajustes Generales"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Pre-cargar valores guardados
        ctx["theme"] = getattr(user, "theme_preference", "system")
        ctx["show_tips"] = getattr(user, "show_tips", True)
        ctx["language"] = getattr(user, "language", "es")
        ctx["timezone"] = getattr(user, "timezone", "UTC")
        ctx["date_format"] = getattr(user, "date_format", "dd/mm/aaaa")
        ctx["number_format"] = getattr(user, "number_format", ".,")
        return ctx

    def post(self, request, *args, **kwargs):
        user = request.user

        # --- Apariencia ---
        if "action_update_appearance" in request.POST:
            theme = request.POST.get("theme", "system")
            tips_enabled = "tips" in request.POST

            user.theme_preference = theme
            user.show_tips = tips_enabled
            user.save()

            messages.success(request, "Preferencias de apariencia guardadas correctamente.")
            return redirect(reverse("panel:ajustes_general"))

        # --- Localización ---
        elif "action_update_locale" in request.POST:
            lang = request.POST.get("lang", "").strip()
            tz = request.POST.get("tz", "").strip()
            date_format = request.POST.get("date_format", "").strip()
            number_format = request.POST.get("number_format", "").strip()

            if not lang or not tz:
                messages.error(request, "Debes seleccionar un idioma y una zona horaria.")
                return redirect(reverse("panel:ajustes_general"))

            try:
                user.language = lang
                user.timezone = tz
                user.date_format = date_format or "dd/mm/aaaa"
                user.number_format = number_format or ".,"
                user.save()
                messages.success(request, "Configuración de localización guardada correctamente.")
            except Exception as e:
                messages.error(request, f"Ocurrió un error al guardar la configuración: {e}")

            return redirect(reverse("panel:ajustes_general"))

        messages.warning(request, "No se reconoció la acción del formulario.")
        return redirect(reverse("panel:ajustes_general"))


# ------------------------------
# CUENTA (Perfil de usuario)
# ------------------------------

class AjustesCuentaView(AjustesBase):
    seccion = "cuenta"
    page_title = "Perfil y Cuenta"

    def post(self, request, *args, **kwargs):
        user = request.user

        # --- Actualizar Perfil ---
        if "action_update_profile" in request.POST:
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            job_title = request.POST.get("job_title", "").strip()
            avatar_file = request.FILES.get("avatar")

            if not first_name or not last_name:
                messages.error(request, "Nombre y apellido son obligatorios.")
                return redirect(reverse("panel:ajustes_cuenta"))

            try:
                user.first_name = first_name
                user.last_name = last_name

                if hasattr(user, "profile"):
                    user.profile.job_title = job_title
                    if avatar_file:
                        avatar_path = handle_uploaded_file(avatar_file, "avatars", f"user_{user.id}")
                        user.profile.avatar = avatar_path
                    user.profile.save()

                user.save()
                messages.success(request, "Perfil actualizado correctamente.")
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error al actualizar el perfil: {e}")

            return redirect(reverse("panel:ajustes_cuenta"))

        # --- Actualizar Email ---
        elif "action_update_email" in request.POST:
            new_email = request.POST.get("email", "").strip()

            if not new_email:
                messages.error(request, "El email no puede estar vacío.")
                return redirect(reverse("panel:ajustes_cuenta"))

            from django.contrib.auth import get_user_model
            User = get_user_model()

            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                messages.error(request, "El email ingresado ya está en uso.")
                return redirect(reverse("panel:ajustes_cuenta"))

            user.email = new_email
            user.save()
            messages.success(request, "Email actualizado correctamente.")
            return redirect(reverse("panel:ajustes_cuenta"))

        return redirect(reverse("panel:ajustes_cuenta"))


# ------------------------------
# PRIVACIDAD Y 2FA
# ------------------------------

class AjustesPrivacidadView(AjustesBase):
    seccion = "privacidad"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user"] = self.request.user
        return ctx

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        user = request.user

        if "action_enable_2fa" in request.POST:
            if "2fa_secret" in request.session:
                del request.session["2fa_secret"]
            return redirect(reverse("panel:ajustes_2fa_setup"))

        elif "action_disable_2fa" in request.POST:
            user.two_fa_enabled = False
            user.two_fa_secret = None
            user.save()
            messages.success(request, "La autenticación de dos factores ha sido deshabilitada.")
            return redirect(reverse("panel:ajustes_privacidad"))

        elif "action_update_privacy" in request.POST:
            share_data = "share_data" in request.POST
            user.share_data = share_data
            user.save()
            messages.success(request, "Preferencias de privacidad guardadas.")
            return redirect(reverse("panel:ajustes_privacidad"))

        return redirect(reverse("panel:ajustes_privacidad"))


class Ajustes2FASetupView(LoginRequiredMixin, TemplateView):
    template_name = "panel/ajustes_2fa_setup.html"
    page_title = "Configurar 2FA"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        secret = self.request.session.get("2fa_secret")
        if not secret:
            secret = pyotp.random_base32()
            self.request.session["2fa_secret"] = secret

        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="SGIDT")
        ctx["secret"] = secret
        ctx["totp_uri"] = totp_uri
        return ctx

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        code = request.POST.get("2fa_code", "").strip()
        secret = request.session.get("2fa_secret")
        user = request.user

        if not secret or not code:
            messages.error(request, "Error de sesión o código no proporcionado.")
            return redirect(reverse("panel:ajustes_privacidad"))

        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            user.two_fa_secret = secret
            user.two_fa_enabled = True
            user.two_fa_recovery_codes = generate_recovery_codes()
            user.save()

            if "2fa_secret" in request.session:
                del request.session["2fa_secret"]

            messages.success(request, "¡Autenticación de dos factores habilitada correctamente!")
            return redirect(reverse("panel:ajustes_2fa_recovery"))
        else:
            messages.error(request, "Código de verificación inválido.")
            return self.get(request, *args, **kwargs)


class Ajustes2FARecoveryView(AjustesBase):
    template_name = "panel/ajustes_2fa_recovery.html"
    seccion = "privacidad"
    page_title = "Códigos de Recuperación 2FA"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        if not user.two_fa_enabled:
            messages.warning(self.request, "La autenticación de dos factores no está habilitada.")
            return redirect(reverse("panel:ajustes_privacidad"))

        ctx["recovery_codes"] = user.two_fa_recovery_codes
        return ctx

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        user = request.user

        if "action_regenerate_codes" in request.POST:
            user.two_fa_recovery_codes = generate_recovery_codes()
            user.save()
            messages.success(request, "Se han generado nuevos códigos de recuperación.")
            return redirect(reverse("panel:ajustes_2fa_recovery"))

        return redirect(reverse("panel:ajustes_2fa_recovery"))


# ------------------------------
# EMPRESA
# ------------------------------

class AjustesEmpresaView(AjustesBase):
    seccion = "empresa"
    page_title = "Datos de la Empresa"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ctx["empresa"] = get_empresa_activa(self.request)
        except Empresa.DoesNotExist:
            ctx["empresa"] = None
        return ctx

    def post(self, request, *args, **kwargs):
        if "action_update_company" not in request.POST:
            return redirect("panel:ajustes_empresa")

        company_rut = request.POST.get("company_rut", "").strip()
        company_name = request.POST.get("company_name", "").strip()
        company_email = request.POST.get("company_email", "").strip()
        company_phone = request.POST.get("company_phone", "").strip()
        company_address = request.POST.get("company_address_1", "").strip()
        company_city = request.POST.get("company_city", "").strip()
        company_country = request.POST.get("company_country", "").strip()
        company_logo = request.FILES.get("company_logo")

        if not company_rut or not company_name:
            messages.error(request, "RUT y Razón Social son obligatorios.")
            return redirect("panel:ajustes_empresa")

        try:
            empresa = get_empresa_activa(request)
            if not empresa:
                messages.error(request, "No se encontró una empresa activa.")
                return redirect("panel:ajustes_empresa")

            empresa.rut = company_rut
            empresa.razon_social = company_name
            empresa.email = company_email
            empresa.telefono = company_phone
            empresa.direccion_1 = company_address
            empresa.ciudad = company_city
            empresa.pais = company_country

            if company_logo:
                logo_path = handle_uploaded_file(company_logo, "logos", f"empresa_{empresa.id}")
                empresa.logo = logo_path

            empresa.save()
            messages.success(request, "Datos de la empresa guardados correctamente.")
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error al guardar la empresa: {e}")

        return redirect("panel:ajustes_empresa")


# ------------------------------
# INTEGRACIONES
# ------------------------------

class AjustesIntegracionesView(AjustesBase):
    seccion = "integraciones"
    page_title = "Integraciones"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["drive_connected"] = GoogleDriveCredential.objects.filter(user=u).exists()
        ctx["dropbox_connected"] = DropboxCredential.objects.filter(user=u).exists()
        return ctx


# ------------------------------
# REDIRECCIONES Y API
# ------------------------------

def ajustes_landing(request):
    return redirect(reverse("panel:ajustes_general"))


@login_required
def check_email_sync_status(request):
    try:
        empresa = get_empresa_activa(request)
        is_configured = bool(empresa and empresa.email_host and empresa.email_user)
        return JsonResponse({"is_configured": is_configured})
    except Exception as e:
        return JsonResponse({"is_configured": False, "error": str(e)})


@require_POST
@login_required
def save_email_sync_config(request):
    try:
        data = json.loads(request.body)
        empresa = get_empresa_activa(request)

        if not empresa:
            return JsonResponse({"status": "error", "message": "No se encontró una empresa activa."}, status=400)

        email_user = data.get("email_user")
        email_password = data.get("password")
        provider = data.get("provider")

        if not all([email_user, email_password, provider]):
            return JsonResponse({"status": "error", "message": "Todos los campos son requeridos."}, status=400)

        if provider == "gmail":
            empresa.email_host = "imap.gmail.com"
            empresa.email_port = 993
        elif provider == "outlook":
            empresa.email_host = "outlook.office365.com"
            empresa.email_port = 993
        else:
            return JsonResponse({"status": "error", "message": "Proveedor de correo no válido."}, status=400)

        empresa.email_user = email_user
        empresa.email_password = email_password
        empresa.email_use_ssl = True
        empresa.save()

        return JsonResponse({"status": "success", "message": "¡Configuración guardada correctamente!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

