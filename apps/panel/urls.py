# apps/panel/urls.py
from django.urls import path

# Vistas del panel (separadas por módulo, en español)
from apps.panel.views.dashboard import DashboardView
from apps.panel.views.docuemntos import DocsView
from apps.panel.views.reportes import ReportsView, ValidationsView
from apps.panel.views.configuracion import SettingsView
from apps.panel.views.ayuda import HelpView, FAQView, StatusView, help_contact, manual_usuario_pdf, chatbot_ask
from apps.panel.views.api import DashboardSummaryApi, DashboardLatestDocsApi

# APIs existentes de documentos
from apps.documentos import views as doc_views

app_name = "panel"

urlpatterns = [
    # Dashboard
    path("", DashboardView.as_view(), name="dashboard"),
    # APIs Dashboard
    path("api/dashboard/summary/", DashboardSummaryApi.as_view(), name="api_dashboard_summary"),
    path("api/dashboard/latest/", DashboardLatestDocsApi.as_view(), name="api_dashboard_latest"),

    # Módulos
    path("documentos/", DocsView.as_view(), name="documentos_page"),
    path("reportes/", ReportsView.as_view(), name="reportes"),
    path("validaciones/", ValidationsView.as_view(), name="validaciones"),
    path("configuraciones/", SettingsView.as_view(), name="configuraciones"),

    # Ayuda / Soporte
    path("ayuda/", HelpView.as_view(), name="ayuda"),
    path("ayuda/faq/", FAQView.as_view(), name="faq"),
    path("ayuda/estado/", StatusView.as_view(), name="estado"),
    path("ayuda/contacto/", help_contact, name="ayuda_contacto"),
    path("ayuda/chatbot/ask/", chatbot_ask, name="chatbot_ask"),

    # Manual de usuario (PDF)
    path("manual.pdf", manual_usuario_pdf, name="manual_pdf"),

    # APIs Documentos (conserva tus endpoints actuales)
    path("documentos/api/list/", doc_views.documentos_list_api, name="documentos_list_api"),
    path("documentos/api/upload/", doc_views.documentos_upload_api, name="documentos_upload_api"),
]
