from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Create your views here.

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "panel/dashboard.html"


class DocsView(TemplateView): 

    template_name = "panel/documentos.html"

class ReportsView(TemplateView): 

    template_name = "panel/reportes.html"

class ValidationsView(TemplateView):

    template_name = "panel/validaciones.html"

class SettingsView(TemplateView):
    template_name = "panel/configuraciones.html"

class HelpView(TemplateView): 

    template_name = "panel/ayuda.html"
