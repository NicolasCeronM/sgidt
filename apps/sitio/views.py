from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.core.mail import EmailMultiAlternatives # <--- IMPORTANTE
from django.template.loader import render_to_string # <--- IMPORTANTE
from django.conf import settings
from django.contrib import messages

class LandingView(TemplateView):
    template_name = "sitio/landing.html"

def contacto_landing(request):
    if request.method == "POST":
        # 1. Honeypot
        if request.POST.get('hp'):
            return redirect('sitio:landing')

        # 2. Capturar datos
        nombre = request.POST.get('name')
        email = request.POST.get('email')
        mensaje = request.POST.get('message')

        # 3. Validar y Enviar
        if nombre and email and mensaje:
            try:
                asunto = f"Contacto Web SGIDT: {nombre}"
                
                # Contexto para el template (lo que usa ayuda_contacto.html)
                context = {
                    'name': nombre,
                    'email': email,
                    'message': mensaje,
                }

                # A. Renderizar el HTML que ya tienes
                # Asegúrate de que el archivo esté en templates/correo/ayuda_contacto.html
                html_content = render_to_string('correo/ayuda_contacto.html', context)
                
                # B. Versión texto plano (opcional, por si falla el HTML)
                text_content = f"Nombre: {nombre}\nEmail: {email}\nMensaje: {mensaje}"

                # C. Configurar el correo
                msg = EmailMultiAlternatives(
                    subject=asunto,
                    body=text_content,
                    from_email=settings.EMAIL_HOST_USER,
                    to=['sgidtchile@gmail.com'], # Tu correo
                )
                
                # D. Adjuntar el diseño HTML
                msg.attach_alternative(html_content, "text/html")
                
                # E. Enviar
                msg.send()
                
                messages.success(request, "¡Mensaje enviado! Nos pondremos en contacto pronto.")
            except Exception as e:
                print(f"Error enviando correo landing: {e}")
                messages.error(request, "Hubo un error al enviar el mensaje. Intenta más tarde.")
        else:
            messages.warning(request, "Por favor completa todos los campos.")

    return redirect('sitio:landing')