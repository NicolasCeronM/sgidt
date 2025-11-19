from django.utils import timezone
from django.contrib.sessions.models import Session
from .models import SesionUsuario
from user_agents import parse

class ActiveSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar la petición
        response = self.get_response(request)

        # Lógica post-respuesta: Registrar sesión si el usuario está autenticado
        if request.user.is_authenticated and request.session.session_key:
            self.update_user_session(request)

        return response

    def update_user_session(self, request):
        session_key = request.session.session_key
        
        # Evitar consultas excesivas: solo actualizar si la sesión existe
        try:
            # Intentamos obtener la sesión actual de Django
            session = Session.objects.get(session_key=session_key)
            
            # Obtenemos IP y User Agent
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            raw_ua = request.META.get('HTTP_USER_AGENT', '')
            user_agent = parse(raw_ua)
            
            # Definir nombre legible
            browser = user_agent.browser.family
            os_name = user_agent.os.family
            device = f"{browser} en {os_name}"
            
            device_type = 'pc'
            if user_agent.is_mobile:
                device_type = 'mobile'
            elif user_agent.is_tablet:
                device_type = 'tablet'

            # Guardar o actualizar SesionUsuario
            SesionUsuario.objects.update_or_create(
                session=session,
                defaults={
                    'user': request.user,
                    'ip': ip,
                    'user_agent': raw_ua[:255], # Truncar si es muy largo
                    'device_name': device,
                    'device_type': device_type,
                    'last_activity': timezone.now()
                }
            )
        except Session.DoesNotExist:
            pass
        except Exception as e:
            # Log silencioso de errores para no interrumpir al usuario
            print(f"Error actualizando sesión: {e}")