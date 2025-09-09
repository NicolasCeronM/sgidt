# apps/documentos/api_urls_legacy.py
from django.urls import path
from . import views  # reusa tus views actuales basadas en login_required

app_name = "documentos_legacy"

urlpatterns = [
    path("list/",   views.documentos_list_api,   name="list"),
    path("upload/", views.documentos_upload_api, name="upload"),
    path("progreso/<int:doc_id>/", views.documentos_progreso_api, name="progreso"),
    path("progreso_batch/", views.documentos_progreso_batch_api, name="progreso_batch"),
]
