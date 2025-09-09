# apps/documentos/selectors.py
from .models import Documento

def documentos_de_empresas(empresa_ids):
    """Query base reutilizable para listar documentos del usuario (multi-empresa)."""
    return Documento.objects.filter(empresa_id__in=list(empresa_ids))
