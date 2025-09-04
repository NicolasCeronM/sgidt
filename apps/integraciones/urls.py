from django.urls import path
from . import views
from . import views as integ_views

app_name = "integraciones"

urlpatterns = [

    # --- Google Drive OAuth ---
    path("google/connect/", views.google_connect, name="google_connect"),
    path("google/callback/", views.google_callback, name="google_callback"),
    path("google/disconnect/", views.google_disconnect, name="google_disconnect"),
    path("google/files/", views.google_files, name="google_files"),

        # --- Dropbox OAuth (DEV) ---
    path("dropbox/connect/",    integ_views.dropbox_connect,    name="dropbox_connect"),
    path("dropbox/callback/",   integ_views.dropbox_callback,   name="dropbox_callback"),
    path("dropbox/disconnect/", integ_views.dropbox_disconnect, name="dropbox_disconnect"),
    path("dropbox/files/",      integ_views.dropbox_files,      name="dropbox_files"),
]
