from __future__ import annotations
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Empresa, EmpresaUsuario, RolEmpresa

Usuario = get_user_model()

def get_empresa_activa(request) -> Empresa:
    eid = request.session.get("empresa_activa_id")
    if eid:
        return get_object_or_404(Empresa, id=eid)
    # fallback: primera empresa donde es miembro
    membership = EmpresaUsuario.objects.filter(usuario=request.user).select_related("empresa").first()
    if membership:
        request.session["empresa_activa_id"] = membership.empresa_id
        return membership.empresa
    raise Empresa.DoesNotExist("No hay empresa activa asociada.")

def user_es_admin_de(request, empresa: Empresa) -> bool:
    return EmpresaUsuario.objects.filter(
        usuario=request.user, empresa=empresa, rol=RolEmpresa.ADMIN
    ).exists()
