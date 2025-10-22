from django.urls import path
from .views import ReporteKpiAPIView

app_name = 'panel_api'

urlpatterns = [
    path('reportes/kpis/', ReporteKpiAPIView.as_view(), name='reportes_kpis'),
]