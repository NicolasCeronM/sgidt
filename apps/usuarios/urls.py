# apps/usuarios/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from .views import VistaLogin, cerrar_sesion, ConfiguracionAdministradorView
from . import views_password_reset as pr_views

app_name = "usuarios"

urlpatterns = [
    # Autenticación propia
    path("login/", VistaLogin.as_view(), name="login"),
    path("logout/", cerrar_sesion, name="logout"),

    # Restablecimiento de contraseña (flujo propio existente)
    path("password/olvido/", pr_views.password_reset_request, name="password_reset_request"),
    path("password/verificar/", pr_views.password_reset_verify, name="password_reset_verify"),
    path("password/nueva/", pr_views.password_reset_set, name="password_reset_set"),

    # Configuración de Administrador
    path("config/admin/", ConfiguracionAdministradorView.as_view(), name="config_admin"),

    # === Cambio de contraseña (usuario autenticado) ===
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="usuarios/password_change_form.html",
            success_url=reverse_lazy("usuarios:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="usuarios/password_change_done.html"
        ),
        name="password_change_done",
    ),
]
