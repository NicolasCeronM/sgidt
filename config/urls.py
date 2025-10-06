# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # --- Administración ---
    path("admin/", admin.site.urls),

    # --- Sitio público ---
    path("", include(("apps.sitio.urls", "sitio"), namespace="sitio")),

    # --- Autenticación / Usuarios / Empresas ---
    path("usuarios/", include(("apps.usuarios.urls", "usuarios"), namespace="usuarios")),
    path("empresas/", include(("apps.empresas.urls", "empresas"), namespace="empresas")),

    # --- Panel interno (todas las páginas del panel) ---
    path("app/", include(("apps.panel.urls", "panel"), namespace="panel")),

    # --- APIs ---
    path("api/v1/documentos/", include("apps.documentos.api.v1.urls")),
    path("api/documentos/", include("apps.documentos.api_urls_legacy")),  # si mantienes compat

    # --- Otras apps de páginas (si las usas) ---
    path("proveedores/", include(("apps.proveedores.urls", "proveedores"), namespace="proveedores")),
    path("correo/", include(("apps.correo.urls", "correo"), namespace="correo")),
    path("integraciones/", include(("apps.integraciones.urls", "integraciones"), namespace="integraciones")),

    # DRF login/logout para sesión (útil en pruebas web)
    path("api/auth/session/", include("rest_framework.urls")),  # /login/ y /logout/
     path("api/", include("apps.usuarios.api_urls", namespace="auth_api")),

    # JWT
    path("api/auth/login/",   TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(),    name="token_refresh"),

    # --- Redirecciones de compatibilidad ---
    path("app/documentos/api/list/",   RedirectView.as_view(url="/api/documentos/list/",   permanent=True)),
    path("app/documentos/api/upload/", RedirectView.as_view(url="/api/documentos/upload/", permanent=True)),

    path("api/v1/sii/", include("apps.sii.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
