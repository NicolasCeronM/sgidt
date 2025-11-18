from __future__ import annotations
import pyotp
from django.core.signing import BadSignature, SignatureExpired
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from .forms import FormularioLogin, UsuarioAdminConfigForm
from apps.empresas.forms import EmpresaAdminConfigForm
from apps.empresas.utils import get_empresa_activa, user_es_admin_de

Usuario = get_user_model()

# Configuración para la cookie de "Confiar en este dispositivo"
TRUSTED_DEVICE_COOKIE_NAME = "sgidt_trusted_device"
TRUSTED_DEVICE_AGE = 60 * 60 * 24 * 30  # 30 días en segundos


class VistaLogin(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = FormularioLogin
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("panel:dashboard")

    def form_valid(self, form):
        """
        Validación personalizada para soporte de 2FA y dispositivos de confianza.
        """
        user = form.get_user()

        # 1. Verificar si el usuario tiene 2FA habilitado
        if user.two_fa_enabled:
            
            # --- Verificar si el dispositivo ya es de confianza (Cookie firmada) ---
            is_device_trusted = False
            try:
                # CORRECCIÓN: Añadimos el 'salt' aquí también para poder leer la cookie correctamente
                cookie_user_id = self.request.get_signed_cookie(
                    TRUSTED_DEVICE_COOKIE_NAME,
                    salt='sgidt-trusted-device',  # <--- ¡ESTO FALTABA!
                    max_age=TRUSTED_DEVICE_AGE
                )
                # Verificamos que la cookie corresponda al usuario que intenta loguearse
                if cookie_user_id == str(user.id):
                    is_device_trusted = True
            except (KeyError, BadSignature, SignatureExpired):
                # Si la cookie no existe, fue alterada o expiró, pedimos 2FA
                is_device_trusted = False
            
            # Si NO es de confianza, procedemos a pedir el código
            if not is_device_trusted:
                otp_code = form.cleaned_data.get("otp_code")
                trust_this_device = form.cleaned_data.get("trust_device")

                # CASO A: El usuario no ha enviado código aún (Primer paso)
                if not otp_code:
                    # Renderizamos la misma página pero indicando que falta 2FA
                    context = self.get_context_data(form=form)
                    context['requires_2fa'] = True
                    return render(self.request, self.template_name, context)

                # CASO B: El usuario envió código, procedemos a validar
                verificado = False
                
                # Validar TOTP (Google Authenticator)
                if user.two_fa_secret:
                    totp = pyotp.TOTP(user.two_fa_secret)
                    if totp.verify(otp_code):
                        verificado = True

                # Validar Códigos de Recuperación (si TOTP falló)
                if not verificado and user.two_fa_recovery_codes:
                    if otp_code in user.two_fa_recovery_codes:
                        verificado = True
                        # Quemamos el código usado por seguridad
                        user.two_fa_recovery_codes.remove(otp_code)
                        user.save(update_fields=["two_fa_recovery_codes"])

                if not verificado:
                    # Código incorrecto -> Volver a mostrar form con error
                    form.add_error('otp_code', 'Código de verificación inválido o expirado.')
                    context = self.get_context_data(form=form)
                    context['requires_2fa'] = True
                    return render(self.request, self.template_name, context)
                
                # --- SI LLEGAMOS AQUÍ, EL CÓDIGO ES VÁLIDO ---
                
                # Logueamos al usuario llamando al padre
                response = super().form_valid(form)
                
                # Si marcó "Confiar en este dispositivo", guardamos la cookie segura
                if trust_this_device:
                    response.set_signed_cookie(
                        TRUSTED_DEVICE_COOKIE_NAME,
                        str(user.id),
                        salt='sgidt-trusted-device',
                        max_age=TRUSTED_DEVICE_AGE,
                        httponly=True, # Seguridad: JS no puede leerla
                        samesite='Lax'
                    )
                return response

        # Si no tiene 2FA o el dispositivo ya era de confianza, login normal
        return super().form_valid(form)


def cerrar_sesion(request):
    logout(request)
    return redirect("usuarios:login")


class ConfiguracionAdministradorView(LoginRequiredMixin, View):
    template_name = "usuarios/config_admin.html"

    def get(self, request):
        empresa = get_empresa_activa(request)
        if not user_es_admin_de(request, empresa):
            messages.error(request, "No tienes permisos de administrador en la empresa activa.")
            return redirect("panel:dashboard")

        f_empresa = EmpresaAdminConfigForm(instance=empresa)
        f_usuario = UsuarioAdminConfigForm(instance=request.user)
        return render(request, self.template_name, {
            "empresa": empresa,
            "f_empresa": f_empresa,
            "f_usuario": f_usuario,
        })

    def post(self, request):
        empresa = get_empresa_activa(request)
        if not user_es_admin_de(request, empresa):
            messages.error(request, "No tienes permisos de administrador en la empresa activa.")
            return redirect("panel:dashboard")

        f_empresa = EmpresaAdminConfigForm(request.POST, request.FILES, instance=empresa)
        f_usuario = UsuarioAdminConfigForm(request.POST, request.FILES, instance=request.user)

        ok = True
        if "guardar_empresa" in request.POST:
            ok = f_empresa.is_valid()
            if ok:
                f_empresa.save()

        if "guardar_usuario" in request.POST:
            ok = f_usuario.is_valid() and ok
            if f_usuario.is_valid():
                f_usuario.save()

        if not ok:
            messages.error(request, "Revisa los campos marcados en rojo.")

        return render(request, self.template_name, {
            "empresa": empresa,
            "f_empresa": f_empresa,
            "f_usuario": f_usuario,
        })