from django.urls import path
from .views import VistaLogin, cerrar_sesion, ConfiguracionAdministradorView
from . import views_password_reset as pr_views

app_name = "usuarios"
urlpatterns = [
    path("login/", VistaLogin.as_view(), name="login"),
    path("logout/", cerrar_sesion, name="logout"),

        # Rutas para restablecimiento de contraseña
    path("password/olvido/", pr_views.password_reset_request, name="password_reset_request"),
    path("password/verificar/", pr_views.password_reset_verify, name="password_reset_verify"),
    path("password/nueva/", pr_views.password_reset_set, name="password_reset_set"),

    # NUEVA: Configuración de Administrador
    path("config/admin/", ConfiguracionAdministradorView.as_view(), name="config_admin"),
]
