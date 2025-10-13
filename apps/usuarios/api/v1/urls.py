# apps/usuarios/api/v1/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

# Si dejaste views_auth.py en la raíz de la app:
from apps.usuarios.views_auth import LoginAPIView, MeAPIView

# Si moviste a usuarios/api/v1/views.py, usar:
# from .views import LoginAPIView, MeAPIView

app_name = "usuarios_api_v1"

urlpatterns = [
    path("auth/login/",   LoginAPIView.as_view(),     name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("auth/me/",      MeAPIView.as_view(),        name="me"),
]
