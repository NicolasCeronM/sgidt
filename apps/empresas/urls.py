# apps/Empresa/urls.py
from django.urls import path
from .views_wizard import RegistroContribuyenteWizardView
from .views import RegistroPyMEView, BuscarEmpresaView

app_name = "empresas"

urlpatterns = [
    # Wizard por pasos:
    path("registro/", RegistroContribuyenteWizardView.as_view(), {"step": 0}, name="registro_wizard"),
    path("registro/<int:step>/", RegistroContribuyenteWizardView.as_view(), name="registro_wizard"),

    # Legacy (a eliminar en el futuro):
    path("registro-legacy/", RegistroPyMEView.as_view(), name="registro_pyme-legacy"),
    path("buscar_empresa/", BuscarEmpresaView.as_view(), name="buscar_empresa"),
]
