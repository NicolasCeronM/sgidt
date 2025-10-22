from typing import Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch

# Ajusta imports a donde estén tus modelos:
from apps.empresas.models import Empresa, EmpresaUsuario, normalizar_rut  # <- ajusta módulo

def resolve_empresa_for_request(request) -> Optional[Empresa]:
    """
    Devuelve la Empresa 'activa' del usuario.
    - Si viene ?empresa_rut=, intenta esa primero.
    - Si no, toma la primera membresía.
    """
    if not request.user.is_authenticated:
        return None

    rut_param = request.query_params.get("empresa_rut") or request.data.get("empresa_rut")
    if rut_param:
        rut = normalizar_rut(rut_param)  # usa tu normalizador
        try:
            # Asegura que el usuario sea miembro de esa empresa
            return Empresa.objects.filter(
                miembros__usuario=request.user, rut=rut
            ).first()
        except ObjectDoesNotExist:
            return None

    membership = (
        EmpresaUsuario.objects
        .select_related("empresa")
        .filter(usuario=request.user)
        .first()
    )
    return membership.empresa if membership else None
