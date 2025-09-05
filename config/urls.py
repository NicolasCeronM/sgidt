"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from apps.panel import views as panel_views

urlpatterns = [
    # --- Administración ---
    path("admin/", admin.site.urls),

    # --- Sitio público ---
    path("", include("apps.sitio.urls", namespace="sitio")),

    # --- Autenticación / Usuarios ---
    path("usuarios/", include("apps.usuarios.urls", namespace="usuarios")),
    path("empresas/", include(("apps.empresas.urls", "empresas"), namespace="empresas")),

    # --- Aplicación interna (solo páginas / templates) ---
    path("app/", include("apps.panel.urls", namespace="panel")),
    path("configuracion/", panel_views.SettingsView.as_view(), name="configuraciones"),

    # --- APIs (solo lógica / JSON) ---
    path("api/documentos/", include(("apps.documentos.api_urls", "documentos"), namespace="documentos")),
    # Si más adelante migras proveedores a API:
    # path("api/proveedores/", include(("apps.proveedores.api_urls", "proveedores"), namespace="proveedores")),

    # --- Rutas de apps que hoy son vistas (si aún las usas como páginas) ---
    path("proveedores/", include(("apps.proveedores.urls", "proveedores"), namespace="proveedores")),

    # --- Correo & Integraciones ---
    path("correo/", include(("apps.correo.urls", "correo"), namespace="correo")),
    path("integraciones/", include(("apps.integraciones.urls", "integraciones"), namespace="integraciones")),

    # --- Compatibilidad con rutas antiguas (redirecciones 301) ---
    path("app/documentos/api/list/",   RedirectView.as_view(url="/api/documentos/list/",   permanent=True)),
    path("app/documentos/api/upload/", RedirectView.as_view(url="/api/documentos/upload/", permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



