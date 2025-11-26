# apps/sitio/urls.py
from django.urls import path
from .views import LandingView, contacto_landing  # <--- Importa la nueva vista

app_name = "sitio"

urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("contacto/", contacto_landing, name="contacto"), # <--- Nueva ruta
]