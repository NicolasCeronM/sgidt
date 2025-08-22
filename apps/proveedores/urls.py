from django.urls import path
from . import views

app_name = "proveedor"

urlpatterns = [
    path("proveedores/", views.proveedores_list, name="proveedores_list"),
    path("proveedores/crear/", views.proveedores_create, name="proveedores_create"),
    path("proveedores/<int:pk>/editar/", views.proveedores_update, name="proveedores_update"),
    path("proveedores/<int:pk>/", views.proveedores_detail, name="proveedores_detail"),
]