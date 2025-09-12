# apps/panel/views/documents.py
from django.views.generic import TemplateView

class DocsView(TemplateView):
    template_name = "panel/documentos.html"
