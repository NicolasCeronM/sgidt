# apps/usuarios/views.py
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib import messages

class LoginUsuario(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True  # si ya está logueado lo manda al home

class LogoutUsuario(LogoutView):
    next_page = reverse_lazy("usuarios:login")

class RegistroUsuario(CreateView):
    template_name = "registro.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("usuarios:login")

    def form_valid(self, form):
        messages.success(self.request, "Cuenta creada correctamente. Ahora puedes iniciar sesión.")
        return super().form_valid(form)
