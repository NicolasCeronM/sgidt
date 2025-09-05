# apps/documentos/api_urls.py
from django.urls import path
from . import views

app_name = "documentos"

urlpatterns = [
    path("list/",   views.documentos_list_api,   name="list"),
    path("upload/", views.documentos_upload_api, name="upload"),
    # Si ya tienes progreso (cuando integres Celery/Redis):
    # path("progreso/<int:doc_id>/", views.documentos_progreso_api, name="progreso"),
]
