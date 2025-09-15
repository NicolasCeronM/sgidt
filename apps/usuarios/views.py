from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import AdminProfileForm, FormularioLogin
from .models import Profile

Usuario = get_user_model()


class VistaLogin(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = FormularioLogin
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("panel:dashboard")


def cerrar_sesion(request):
    logout(request)
    return redirect("usuarios:login")


# ========= Configuración de perfil (una sola vista) =========
@login_required
def admin_configuracion(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = AdminProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            # 👇 considera el "clear" de avatar/logo como cambio
            cleared = ('avatar-clear' in request.POST) or ('empresa_logo-clear' in request.POST)
            if not form.has_changed() and not cleared:
                messages.info(request, "No hiciste cambios.")
                return redirect("usuarios:admin_configuracion")

            form.save()
            return redirect("usuarios:admin_configuracion")
        messages.error(request, "Revisa los campos marcados.")
    else:
        form = AdminProfileForm(instance=profile, user=request.user)

    return render(request, "usuarios/admin_configuracion.html", {"form": form})
