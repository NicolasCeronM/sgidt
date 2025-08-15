from django.urls import path
from .views import HomeView, DocsView, ReportsView, ValidationsView, SettingsView, HelpView

app_name = "pages"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("documentos/", DocsView.as_view(), name="documentos"),
    path("reportes/", ReportsView.as_view(), name="reportes"),
    path("validaciones/", ValidationsView.as_view(), name="validaciones"),
    path("configuraciones/", SettingsView.as_view(), name="configuraciones"),
    path("ayuda/", HelpView.as_view(), name="ayuda"),
]