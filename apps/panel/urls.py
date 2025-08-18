from django.urls import path
from .views import DashboardView
from .views import DashboardView, DocsView, ReportsView, ValidationsView, SettingsView, HelpView
from apps.documentos import views as doc_views
app_name = "panel"
urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    
    path("reportes/", ReportsView.as_view(), name="reportes"),
    path("validaciones/", ValidationsView.as_view(), name="validaciones"),
    path("configuraciones/", SettingsView.as_view(), name="configuraciones"),
    path("ayuda/", HelpView.as_view(), name="ayuda"),
    #Documentos
    path("documentos/", doc_views.documentos_page, name="documentos_page"),
    path("documentos/api/list/", doc_views.documentos_list_api, name="documentos_list_api"),
    path("documentos/api/upload/", doc_views.documentos_upload_api, name="documentos_upload_api"),
]