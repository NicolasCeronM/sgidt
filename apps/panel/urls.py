# apps/panel/urls.py
from django.urls import path

# Vistas del panel (separadas por módulo, en español)
from apps.panel.views.dashboard import DashboardView, GastosUltimos6MesesAPI
from apps.panel.views.docuemntos import DocsView
from apps.panel.views.reportes import ReportsView, export_report_data, ValidationsView
# ELIMINAR: from apps.panel.views.configuracion import SettingsView, check_email_sync_status, save_email_sync_config
from apps.panel.views.ayuda import HelpView, FAQView, StatusView, help_contact, manual_usuario_pdf, chatbot_ask
from apps.panel.views.api import DashboardSummaryApi, DashboardLatestDocsApi

# MODIFICAR: Importar las nuevas vistas y APIs de ajustes.py
from apps.panel.views.ajustes import (
    AjustesGeneralView, AjustesCuentaView, AjustesPrivacidadView, ajustes_landing,
    AjustesIntegracionesView, AjustesEmpresaView,
    check_email_sync_status, save_email_sync_config, Ajustes2FASetupView, Ajustes2FARecoveryView,
    desconectar_email_sync
)

# APIs existentes de documentos
from apps.documentos import views as doc_views


app_name = "panel"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("api/dashboard/summary/", DashboardSummaryApi.as_view(), name="api_dashboard_summary"),
    path("api/dashboard/latest/", DashboardLatestDocsApi.as_view(), name="api_dashboard_latest"),
    path("api/dashboard/gastos6m/", GastosUltimos6MesesAPI.as_view(), name="api_dashboard_gastos6m"),

    path("documentos/", DocsView.as_view(), name="documentos_page"),
    path("validaciones/", ValidationsView.as_view(), name="validaciones"),
    
    # ELIMINAR: Ruta de configuraciones
    # path("configuraciones/", SettingsView.as_view(), name="configuraciones"),

    # RUTAS DE AJUSTES UNIFICADAS
    path("ajustes/", ajustes_landing, name="ajustes"),
    path("ajustes/general/", AjustesGeneralView.as_view(), name="ajustes_general"),
    path("ajustes/cuenta/", AjustesCuentaView.as_view(), name="ajustes_cuenta"),
    path("ajustes/privacidad/", AjustesPrivacidadView.as_view(), name="ajustes_privacidad"),
    # NUEVAS RUTAS
    path("ajustes/empresa/", AjustesEmpresaView.as_view(), name="ajustes_empresa"),
    path("ajustes/integraciones/", AjustesIntegracionesView.as_view(), name="ajustes_integraciones"),

    path("reportes/", ReportsView.as_view(), name="reportes"),
    path("reportes/exportar/<str:file_type>/", export_report_data, name="exportar_reporte"),

    # Estas rutas ahora apuntan a las vistas importadas de ajustes.py
    path("api/check-email-sync-status/", check_email_sync_status, name="check_email_sync_status"),
    path("api/save-email-sync-config/", save_email_sync_config, name="save_email_sync_config"),

    path("ayuda/", HelpView.as_view(), name="ayuda"),
    path("ayuda/faq/", FAQView.as_view(), name="faq"),
    path("ayuda/estado/", StatusView.as_view(), name="estado"),
    path("ayuda/contacto/", help_contact, name="ayuda_contacto"),
    path("ayuda/chatbot/ask/", chatbot_ask, name="chatbot_ask"),

    path("manual.pdf", manual_usuario_pdf, name="manual_pdf"),

    path("documentos/api/list/", doc_views.documentos_list_api, name="documentos_list_api"),
    path("documentos/api/upload/", doc_views.documentos_upload_api, name="documentos_upload_api"),

    # --- RUTA PARA CONFIGURACIÓN 2FA ---
    path("ajustes/2fa/setup/", Ajustes2FASetupView.as_view(), name="ajustes_2fa_setup"),
    path("ajustes/2fa/recovery/", Ajustes2FARecoveryView.as_view(), name="ajustes_2fa_recovery"),

    # --- RUTA PARA DESCONECTAR SINCRONIZACIÓN DE EMAIL ---
    path("api/disconnect-email-sync/", desconectar_email_sync, name="desconectar_email"),

]