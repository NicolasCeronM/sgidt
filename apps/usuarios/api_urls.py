from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views_auth import LoginAPIView, MeAPIView

app_name = "auth_api"

urlpatterns = [
    path("auth/login/",   LoginAPIView.as_view(),     name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("auth/me/",      MeAPIView.as_view(),        name="me"),
]
