from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Sitio público / landings
    path("", include("apps.sitio.urls")),

    # Panel (solo HTML)
    path("panel/", include("apps.panel.urls")),

    # Auth y web de usuarios (HTML)
    path("usuarios/", include("apps.usuarios.urls")),

    # Apps web (HTML)
    path("empresas/", include("apps.empresas.urls")),
    path("proveedores/", include("apps.proveedores.urls")),
    path("integraciones/", include("apps.integraciones.urls")),
    path("sii-web/", include("apps.sii.urls")),  # si quieres mantener vistas HTML de pruebas

    path("admin/", admin.site.urls),

    # APIs (todo DRF bajo /api/v1/)
    path("api/v1/", include("config.api_v1")),  # <- un router centralizado
]
# path("api/v1/auth/", include("rest_framework.urls")),  # <- si usas browsable API