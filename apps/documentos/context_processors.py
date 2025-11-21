from apps.empresas.models import Empresa
from apps.documentos.services.alerts import get_empresa_alerts

def alertas_counter(request):
    """
    Cuenta las alertas totales para mostrarlas en el menú lateral.
    """
    # Solo funciona si el usuario ha iniciado sesión
    if not request.user.is_authenticated:
        return {}

    # Obtenemos la empresa de la sesión del usuario
    # (Ajusta 'empresa_id' si usas otro nombre de variable en tu sesión)
    empresa_id = request.session.get('empresa_id') 
    
    count = 0
    if empresa_id:
        try:
            empresa = Empresa.objects.get(pk=empresa_id)
            # Reutilizamos tu servicio de alertas existente
            alertas = get_empresa_alerts(empresa)
            count = alertas['total']
        except Empresa.DoesNotExist:
            count = 0

    # Esta variable {{ total_alertas_sidebar }} estará disponible en TODO el HTML
    return {'total_alertas_sidebar': count}