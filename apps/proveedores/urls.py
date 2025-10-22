# apps/proveedores/urls.py
from django.urls import path
from . import views

app_name = "proveedores"

urlpatterns = [
    path("", views.proveedores_list, name="proveedores_list"),
    path("crear/", views.proveedores_create, name="proveedores_create"),
    path("<int:pk>/editar/", views.proveedores_update, name="proveedores_update"),
    path("<int:pk>/", views.proveedores_detail, name="proveedores_detail"),
    path("<int:pk>/eliminar/", views.proveedores_delete, name="proveedores_delete"),
]
