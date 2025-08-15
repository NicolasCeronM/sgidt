# apps/usuarios/urls.py
from django.urls import path
from .views import LoginUsuario, LogoutUsuario, RegistroUsuario

app_name = "usuarios"

urlpatterns = [
    path("login/", LoginUsuario.as_view(), name="login"),
    path("logout/", LogoutUsuario.as_view(), name="logout"),
    path("registro/", RegistroUsuario.as_view(), name="registro"),
]
