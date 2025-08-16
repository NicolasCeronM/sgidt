from django.urls import path
from .views import VistaLogin, cerrar_sesion, registro_persona, registro_empresa

app_name = "usuarios"
urlpatterns = [
    path("login/", VistaLogin.as_view(), name="login"),
    path("logout/", cerrar_sesion, name="logout"),
    path("registro/persona/", registro_persona, name="registro_persona"),
    path("registro/empresa/", registro_empresa, name="registro_empresa"),
]
