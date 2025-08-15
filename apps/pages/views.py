from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.

class HomeView(TemplateView): 

    template_name = "pages/home.html"

class DocsView(TemplateView): 

    template_name = "pages/documentos.html"

class ReportsView(TemplateView): 

    template_name = "pages/reportes.html"

class ValidationsView(TemplateView):

    template_name = "pages/validaciones.html"

class SettingsView(TemplateView):
    template_name = "pages/configuraciones.html"

class HelpView(TemplateView): 

    template_name = "pages/ayuda.html"
