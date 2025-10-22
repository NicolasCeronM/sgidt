# apps/Empresa/views_wizard.py
from typing import Dict, Any, List, Tuple
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.conf import settings

from .models_contribuyente import Contribuyente, TipoContribuyente
from .forms_wizard import (
    Paso1TipoForm, Paso2IdentificacionForm, Paso3DatosTributariosForm,
    Paso4EmisionForm, Paso5RepresentacionForm, Paso6UsuarioAdminForm, Paso7ConfirmacionForm
)
from .models import Empresa, EmpresaUsuario, RolEmpresa
from datetime import date, datetime
from decimal import Decimal
from datetime import date, datetime
from decimal import Decimal
import logging
from django.contrib.auth import authenticate
from django.db import IntegrityError


User = get_user_model()
WKEY = "registro_contribuyente_data"
logger = logging.getLogger(__name__)


def _to_jsonable(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


class RegistroContribuyenteWizardView(View):
    """
    Wizard server-side por pasos. Persistimos datos en sesión hasta confirmar.
    """
    template_name = "usuarios/registro_wizard.html"

    FORMS: List[Tuple[str, Any]] = [
        ("tipo", Paso1TipoForm),
        ("identificacion", Paso2IdentificacionForm),
        ("datos_tributarios", Paso3DatosTributariosForm),
        ("emision", Paso4EmisionForm),
        ("representacion", Paso5RepresentacionForm),
        ("usuario_admin", Paso6UsuarioAdminForm),
        ("confirmacion", Paso7ConfirmacionForm),
    ]

    # ---------- utilidades ----------
    def _get_data(self, request) -> Dict[str, Any]:
        return request.session.get(WKEY, {})

    def _save_data(self, request, key: str, value: Dict[str, Any]) -> None:
        data = self._get_data(request)
        data[key] = value
        request.session[WKEY] = _to_jsonable(data)


    def _clear(self, request) -> None:
        if WKEY in request.session:
            del request.session[WKEY]

    def _steps_for_tipo(self, data: Dict[str, Any]) -> List[Tuple[str, Any]]:
        """
        Permite saltar 'representacion' cuando no es PJ
        """
        steps = list(self.FORMS)
        tipo = (data.get("tipo") or {}).get("tipo")
        if tipo and tipo != TipoContribuyente.PJ:
            # remover el paso 'representacion'
            steps = [s for s in steps if s[0] != "representacion"]
        return steps

    # ---------- HTTP ----------
    def get(self, request, step: int = 0):
        data = self._get_data(request)
        steps = self._steps_for_tipo(data)
        step = max(0, min(int(step), len(steps) - 1))
        key, form_class = steps[step]
        tipo_actual = (data.get("tipo") or {}).get("tipo")
        try:
            form = form_class(initial=data.get(key, {}), tipo_actual=tipo_actual)
        except TypeError:
            form = form_class(initial=data.get(key, {}))
        # pasa tipo_actual al form si lo soporta
        try:
            form = form_class(initial=data.get(key, {}), tipo_actual=tipo_actual)
        except TypeError:
            form = form_class(initial=data.get(key, {}))
        form = form_class(initial=data.get(key, {}))
        ctx = {
            "step": step,
            "steps": [s[0] for s in steps],
            "form": form,
            "total": len(steps),
            "data": data,
            "tipo_actual": tipo_actual,  # ← nuevo
        }
        return render(request, self.template_name, ctx)

    def post(self, request, step: int = 0):
        data = self._get_data(request)
        steps = self._steps_for_tipo(data)
        step = max(0, min(int(step), len(steps) - 1))
        key, form_class = steps[step]
        tipo_actual = (data.get("tipo") or {}).get("tipo")
        try:
            form = form_class(request.POST, tipo_actual=tipo_actual)
        except TypeError:
            form = form_class(request.POST)
        form = form_class(request.POST)
        if not form.is_valid():
            ctx = {
                "step": step,
                "steps": [s[0] for s in steps],
                "form": form,
                "total": len(steps),
                "data": data,
                "tipo_actual": tipo_actual,  # ← nuevo
            }
            return render(request, self.template_name, ctx)

        # guardar valores validados
        self._save_data(request, key, form.cleaned_data)
        data = self._get_data(request)  # recarga

        # último paso => crear entidades
        if step == len(steps) - 1:
            try:
                with transaction.atomic():
                    return self._crear_entidades_y_login(request, data)
            except Exception as e:
                messages.error(request, f"Ocurrió un error al finalizar el registro: {e}")
                return redirect("empresas:registro_wizard", step=0)

        return redirect("empresas:registro_wizard", step=step + 1)

    # ---------- creación de entidades ----------
    def _crear_entidades_y_login(self, request, data: Dict[str, Any]):
        tipo = data["tipo"]["tipo"]
        ident = data["identificacion"]
        trib = data.get("datos_tributarios", {})
        emi = data.get("emision", {})
        rep = data.get("representacion", {})
        adm = data["usuario_admin"]

        # parse seguro de fecha desde sesión (puede venir 'YYYY-MM-DD' o None)
        fi = trib.get("fecha_inicio_actividades")
        if isinstance(fi, str) and fi:
            try:
                fi = date.fromisoformat(fi)
            except ValueError:
                fi = None

        contrib = Contribuyente.objects.create(
            tipo=tipo,
            rut=ident["rut"],
            razon_social=ident["razon_social"],
            nombre_fantasia=ident.get("nombre_fantasia") or "",
            actividad_economica=trib.get("actividad_economica") or "",
            fecha_inicio_actividades=fi,  # ← usamos la fecha parseada
            domicilio_calle=trib.get("domicilio_calle") or "",
            domicilio_numero=trib.get("domicilio_numero") or "",
            domicilio_comuna=trib.get("domicilio_comuna") or "",
            domicilio_region=trib.get("domicilio_region") or "",
            sistema_facturacion=emi.get("sistema_facturacion") or "",
            certificado_usa=emi.get("certificado_usa") or False,
            tipos_dte_autorizados=emi.get("tipos_dte_autorizados") or [],
            solo_honorarios=(tipo == TipoContribuyente.PN_HONORARIOS),
            habilitado_dte=(tipo in [TipoContribuyente.PN_GIRO, TipoContribuyente.PJ]),
            tasa_retencion_honorarios=emi.get("tasa_retencion_honorarios"),
            rep_rut=rep.get("rep_rut") or "",
            rep_nombre=rep.get("rep_nombre") or "",
        )

        # Empresa (workspace) — reusa tus campos; copia lo esencial
        empresa = Empresa.objects.create(
            contribuyente=contrib,
            # Si tu Empresa tiene estos campos, se copian:
            razon_social=getattr(contrib, "razon_social", ""),
            rut=getattr(contrib, "rut", None) if hasattr(Empresa, "rut") else None,
        )

        # Usuario admin
        email = adm["email"].lower().strip()
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=adm["nombre"],
            last_name=adm.get("apellido") or "",
            password=adm["password1"],
        )
        # si tu modelo de usuario tiene 'rut' único:
        if hasattr(user, "rut"):
            setattr(user, "rut", adm["rut_personal"])
            user.save(update_fields=["rut"])

        # Marca tipo_contribuyente del usuario si existe (opcional)
        if hasattr(user, "tipo_contribuyente"):
            setattr(user, "tipo_contribuyente", "empresa")  # admin de workspace
            user.save(update_fields=["tipo_contribuyente"])

        # Membresía/rol
        EmpresaUsuario.objects.create(usuario=user, empresa=empresa, rol=RolEmpresa.ADMIN)

        # Login + set empresa activa
        backend = getattr(settings, "AUTHENTICATION_BACKENDS", ["django.contrib.auth.backends.ModelBackend"])[0]
        login(request, user, backend=backend)
        request.session["empresa_activa_id"] = empresa.id

        # limpiezas
        self._clear(request)
        messages.success(request, "¡Registro completado con éxito!")
        return redirect("panel:dashboard")
