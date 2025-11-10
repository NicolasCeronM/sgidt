from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.urls import reverse

class AjustesBase(LoginRequiredMixin, TemplateView):
    template_name = "panel/ajustes.html"
    seccion = "general"
    page_title = "Ajustes"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["seccion"] = self.seccion
        ctx["page_title"] = self.page_title
        return ctx

class AjustesGeneralView(AjustesBase):
    seccion = "general"

class AjustesCuentaView(AjustesBase):
    seccion = "cuenta"

class AjustesPrivacidadView(AjustesBase):
    seccion = "privacidad"

def ajustes_landing(request):
    return redirect(reverse("panel:ajustes_general"))

