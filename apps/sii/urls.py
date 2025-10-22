# apps/sii/urls.py
from django.urls import path
from .views import (
    ConsultaContribuyenteView, ValidarDTEView, EstadoDTEView, RecibirDTEView
)

app_name = "sii"

urlpatterns = [
    path("contribuyente/", ConsultaContribuyenteView.as_view(), name="contribuyente"),
    path("validar-dte/",   ValidarDTEView.as_view(),           name="validar_dte"),
    path("estado-dte/",    EstadoDTEView.as_view(),            name="estado_dte"),
    path("recibir-dte/",   RecibirDTEView.as_view(),           name="recibir_dte"),
]
