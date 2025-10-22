# apps/empresas/views.py
from __future__ import annotations
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.shortcuts import render, redirect
from django.views import View
from .forms import RegistroPyMEForm
import requests
from django.http import JsonResponse

class BuscarEmpresaView(View):
    def get(self, request):
        rut = request.GET.get("rut")
        if not rut:
            return JsonResponse({"error": "Debe proporcionar un RUT"}, status=400)
 
        url = "https://sre.cl/api/company_info"
        params = {
            "token": "dbad0503-18c6-4100-825f-abf87f6f01e6",
            "rut": rut,
            "actualizado": "False"
        }
        headers = {"Accept": "application/json"}
 
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
 


class RegistroPyMEView(View):
    template_name = "usuarios/registro.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RegistroPyMEForm()})

    def post(self, request):
        form = RegistroPyMEForm(request.POST)
        if not form.is_valid():
            # ❗ Siempre devolver algo
            return render(request, self.template_name, {"form": form})

        try:
            with transaction.atomic():
                empresa, user, membership = form.save()
        except Exception as e:
            messages.error(request, f"Ocurrió un error creando la cuenta: {e}")
            # ❗ Siempre devolver algo
            return render(request, self.template_name, {"form": form})

        # ---- Login seguro: autenticar y luego loguear ----
        # OJO: si tu Usuario hereda de AbstractUser, en el save pusimos username=email.
        raw_password = form.cleaned_data["password1"]
        auth_user = authenticate(
            request,
            username=user.username,   # user.username es el email que setearon en create_user
            password=raw_password,
        )

        if auth_user is not None:
            login(request, auth_user)  # OK: user.backend queda seteado por authenticate
        else:
            # Fallback si tienes múltiples backends y authenticate no devolvió user
            backend = settings.AUTHENTICATION_BACKENDS[0]
            login(request, user, backend=backend)

        # Empresa activa para filtrar todo el panel
        request.session["empresa_activa_id"] = empresa.id
        messages.success(request, "¡Tu PyME fue creada con éxito! Bienvenido/a.")

        # ❗ Siempre devolver algo
        return redirect("panel:dashboard")  # ajusta a tu ruta real
