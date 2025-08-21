from django.shortcuts import render

# Create your views here.
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

# Intento de inline CSS si existe premailer + staticfiles
def _render_html_con_css_inline(request, template, context):
    html = render_to_string(template, context)

    # Intenta inyectar CSS de /static/correo/css/bienvenida.css y convertir a inline
    try:
        from django.contrib.staticfiles import finders
        css_path = finders.find("correo/css/bienvenida.css")
        if css_path:
            with open(css_path, "r", encoding="utf-8") as f:
                css = f.read()
            html = html.replace("</head>", f'<style type="text/css">{css}</style></head>')
        try:
            from premailer import transform
            base_url = getattr(settings, "SITE_URL", request.build_absolute_uri("/"))
            html = transform(html, base_url=base_url)
        except Exception:
            pass
    except Exception:
        pass

    return html


@login_required
def test_form(request):
    """Formulario simple para probar preview/enviar."""
    return render(request, "correo/test.html")


@login_required
def preview_bienvenida(request):
    """Muestra el HTML del correo en el navegador (para diseño)."""
    to = request.GET.get("to") or request.user.email
    ctx = {
        "user": request.user,
        "panel_url": request.build_absolute_uri(reverse("panel:dashboard")),
        "logo_url": request.build_absolute_uri(static("img/logo.png")),
        "now": timezone.now(),
        "to": to,
    }
    html = _render_html_con_css_inline(request, "correo/bienvenida.html", ctx)
    return HttpResponse(html)


@login_required
def enviar_bienvenida_prueba(request):
    """Envía el correo de bienvenida de prueba al email indicado."""
    if request.method != "POST":
        return HttpResponseBadRequest("Método no permitido")

    to = request.POST.get("to") or request.user.email
    if not to:
        messages.error(request, "Debes indicar un correo destino.")
        return redirect(reverse("correo:test_form"))

    ctx = {
        "user": request.user,
        "panel_url": request.build_absolute_uri(reverse("panel:dashboard")),
        "logo_url": request.build_absolute_uri(static("img/logo.png")),
        "now": timezone.now(),
    }

    html = _render_html_con_css_inline(request, "correo/bienvenida.html", ctx)
    text = render_to_string("correo/bienvenida.txt", ctx)

    from_email = (
        getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or getattr(settings, "EMAIL_HOST_USER", None)
        or "no-reply@localhost"
    )

    email = EmailMultiAlternatives(
        subject="(PRUEBA) ¡Bienvenido a SGIDT!",
        body=text,
        from_email=from_email,
        to=[to],
    )
    email.attach_alternative(html, "text/html")
    try:
        email.send(fail_silently=False)
        messages.success(request, f"Correo de prueba enviado a {to}.")
    except Exception as e:
        messages.error(request, f"No se pudo enviar: {e}")

    return redirect(reverse("correo:test_form"))
