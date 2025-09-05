from django.urls import path
from .views import (
    DashboardView, DocsView, ReportsView, ValidationsView, SettingsView,
    HelpView, help_contact, FAQView, StatusView,
    manual_usuario_pdf,   
)
from apps.documentos import views as doc_views

app_name = "panel"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),

    path("reportes/", ReportsView.as_view(), name="reportes"),
    path("validaciones/", ValidationsView.as_view(), name="validaciones"),
    path("configuraciones/", SettingsView.as_view(), name="configuraciones"),

    # === Ayuda y Soporte ===
    path("ayuda/", HelpView.as_view(), name="ayuda"),
    path("ayuda/contacto/", help_contact, name="ayuda_contacto"),
    path("ayuda/faq/", FAQView.as_view(), name="faq"),
    path("ayuda/estado/", StatusView.as_view(), name="estado"),

    # PDF Manual
    path("manual.pdf", manual_usuario_pdf, name="manual_pdf"),

    # Documentos
    path("documentos/", DocsView.as_view(), name="documentos_page"),
    path("documentos/api/list/", doc_views.documentos_list_api, name="documentos_list_api"),
    path("documentos/api/upload/", doc_views.documentos_upload_api, name="documentos_upload_api"),
]
