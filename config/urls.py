from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Sitio público / landings
    path("", include("apps.sitio.urls")),
    path("correo/", include("apps.correo.urls", namespace="correo")),

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
