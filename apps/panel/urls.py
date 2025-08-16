from django.urls import path
from .views import DashboardView
from .views import DashboardView, DocsView, ReportsView, ValidationsView, SettingsView, HelpView
app_name = "panel"
urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("documentos/", DocsView.as_view(), name="documentos"),
    path("reportes/", ReportsView.as_view(), name="reportes"),
    path("validaciones/", ValidationsView.as_view(), name="validaciones"),
    path("configuraciones/", SettingsView.as_view(), name="configuraciones"),
    path("ayuda/", HelpView.as_view(), name="ayuda"),
]