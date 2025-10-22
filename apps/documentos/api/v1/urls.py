# apps/documentos/api/v1/urls.py
from rest_framework.routers import SimpleRouter
from django.urls import path
from .views import DocumentoViewSet, presign_upload

router = SimpleRouter()
router.register(r"", DocumentoViewSet, basename="documentos")

urlpatterns = [
    path("presign-upload/", presign_upload, name="presign_upload"),
]
urlpatterns += router.urls
