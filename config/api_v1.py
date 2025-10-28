# config/api_v1.py
from django.urls import path, include

urlpatterns = [
    path("documentos/", include("apps.documentos.api.v1.urls")),
    path("panel/", include("apps.panel.api.v1.urls")),
    # path("empresas/", include("apps.empresas.api.v1.urls")),          # crear si aplica
    # path("proveedores/", include("apps.proveedores.api.v1.urls")),    # crear si aplica
    path("usuarios/", include("apps.usuarios.api.v1.urls")),          # crear (auth/profile)
    path("sii/", include("apps.sii.api.v1.urls")),                    # mover aquí las de validación real
    # path("dashboard/", include("apps.panel.api.v1.urls")),            # mover APIs de dashboard aquí
    # path("integraciones/", include("apps.integraciones.api.v1.urls")),# opcional
]
