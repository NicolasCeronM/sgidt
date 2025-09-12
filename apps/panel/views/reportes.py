# apps/panel/views/reports.py
from django.views.generic import TemplateView

class ReportsView(TemplateView):
    template_name = "panel/reportes.html"

class ValidationsView(TemplateView):
    template_name = "panel/validaciones.html"
