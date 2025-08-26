from django.urls import path
from .views import RegistroPyMEView

app_name = "empresas"

urlpatterns = [
    path("registro/", RegistroPyMEView.as_view(), name="registro_pyme"),
]
