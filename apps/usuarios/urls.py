from django.urls import path
from .views import VistaLogin, cerrar_sesion

app_name = "usuarios"
urlpatterns = [
    path("login/", VistaLogin.as_view(), name="login"),
    path("logout/", cerrar_sesion, name="logout"),
]
