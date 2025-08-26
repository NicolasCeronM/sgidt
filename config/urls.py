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
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from apps.panel import views as panel_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Público
    path("", include("apps.sitio.urls", namespace="sitio")),             # /

    # Autenticación
    path("usuarios/", include("apps.usuarios.urls", namespace="usuarios")),
    path("empresas/", include(("apps.empresas.urls", "empresas"), namespace="empresas")),

    # App privada
    path("app/", include("apps.panel.urls", namespace="panel")),         # /app/
    path("proveedor/", include(("apps.proveedores.urls"))),
    path("configuracion/", panel_views.configuraciones, name="configuraciones"),

    #correo
    path("correo/", include("apps.correo.urls", namespace="correo")),

    # Integraciones
    path("integraciones/", include("apps.integraciones.urls", namespace="integraciones")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


