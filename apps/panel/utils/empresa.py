# apps/panel/utils/empresa.py
from apps.empresas.models import EmpresaUsuario

def get_empresa_activa(request):
    """
    Retorna la empresa activa del usuario autenticado.
    - Respeta empresa_id en sesión si existe.
    - Si no, toma la primera por fecha de membresía.
    """
    empresa_id = request.session.get("empresa_id")
    qs = (
        EmpresaUsuario.objects
        .select_related("empresa")
        .filter(usuario=request.user)
    )
    eu = qs.filter(empresa_id=empresa_id).first() if empresa_id else qs.order_by("creado_en").first()
    return eu.empresa if eu else None
