from django.urls import path
from . import views

app_name = "correo"

urlpatterns = [
    path("test/", views.test_form, name="test_form"),
    path("preview/", views.preview_bienvenida, name="preview_bienvenida"),
    path("enviar/", views.enviar_bienvenida_prueba, name="enviar_bienvenida_prueba"),
    path("trigger-scan/", views.trigger_email_scan, name="trigger_email_scan"),
]
