# apps/sii/api/v1/urls.py

from django.urls import path
from apps.sii.views import (
    ConsultaContribuyenteView,
    ValidarDTEView,
    EstadoDTEView,
    RecibirDTEView,
)

app_name = "sii_api"

urlpatterns = [
    # GET /api/v1/sii/contribuyente/?rut=76333222-1
    path("contribuyente/",ConsultaContribuyenteView.as_view(),name="consulta-contribuyente",),
    # POST /api/v1/sii/validar-dte/
    path("validar-dte/",ValidarDTEView.as_view(),name="validar-dte",),
    # GET /api/v1/sii/estado-dte/?track_id=a1b2c3d4e5
    path("estado-dte/",EstadoDTEView.as_view(),name="estado-dte",),
    # POST /api/v1/sii/recibir-dte/
    path("recibir-dte/",RecibirDTEView.as_view(),name="recibir-dte",),
]