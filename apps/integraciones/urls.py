from django.urls import path
from . import views

app_name = "integraciones"

urlpatterns = [
    path("google/connect/", views.google_connect, name="google_connect"),
    path("google/callback/", views.google_callback, name="google_callback"),
    path("google/disconnect/", views.google_disconnect, name="google_disconnect"),
    path("google/upload-demo/", views.google_upload_demo, name="google_upload_demo"),
    path("google/files/", views.google_files, name="google_files"),
]
