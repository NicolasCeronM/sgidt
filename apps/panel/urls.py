from django.urls import path
from .views import (
    DashboardView, ReportsView, ValidationsView, SettingsView,
    HelpView, FAQView, StatusView,
    DocumentosPageView, HelpContactView,
)

app_name = "panel"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),

    path("documentos/", DocumentosPageView.as_view(), name="documentos_page"),
    path("reportes/", ReportsView.as_view(), name="reportes"),
    path("validaciones/", ValidationsView.as_view(), name="validaciones"),
    path("configuraciones/", SettingsView.as_view(), name="configuraciones"),

    path("ayuda/", HelpView.as_view(), name="ayuda"),
    path("ayuda/faq/", FAQView.as_view(), name="faq"),
    path("ayuda/estado/", StatusView.as_view(), name="estado"),
    path("ayuda/contacto/", HelpContactView.as_view(), name="ayuda_contacto"),
]
