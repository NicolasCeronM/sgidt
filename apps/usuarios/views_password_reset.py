# apps/usuarios/views_password_reset.py
import random
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.templatetags.static import static

from .forms import (
    PasswordResetRequestForm,
    PasswordResetVerifyForm,
    PasswordResetSetForm,
)
from .models import PasswordResetCode

User = get_user_model()


def _generate_code():
    # 6 dígitos, con ceros a la izquierda si corresponde
    return f"{random.randint(0, 999999):06d}"


def _send_reset_email(request, email, code):
    """
    Envía correo HTML + texto con el código.
    """
    subject = "Tu código para restablecer la contraseña"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    # URLs absolutas (para logo y CTA)
    logo_url = request.build_absolute_uri(static("sitio/img/logo_sgidt.png"))
    verify_url = request.build_absolute_uri(reverse("usuarios:password_reset_verify"))
    # (opcional) prellenar email por querystring
    verify_url = f"{verify_url}?email={quote(email)}"

    context = {
        "site_name": "SGIDT",
        "code": code,
        "code_spaced": " ".join(list(code)),
        "email": email,
        "logo_url": logo_url,
        "verify_url": verify_url,
        "support_email": "sgidtchile@gmail.com",
    }

    html_body = render_to_string("correo/password_reset_code.html", context)
    text_body = (
        "Hola,\n\n"
        "Recibimos una solicitud para restablecer tu contraseña en SGIDT.\n"
        f"Tu código de verificación es: {code}\n\n"
        "Este código expira en 10 minutos.\n"
        f"Puedes ingresar el código aquí: {verify_url}\n\n"
        "Si tú no solicitaste esto, ignora este correo.\n\n"
        "Saludos,\nEquipo SGIDT"
    )

    msg = EmailMultiAlternatives(subject, text_body, from_email, [email])
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def password_reset_request(request):
    """
    Paso 1: el usuario ingresa su correo. Si existe, generamos y enviamos código.
    """
    form = PasswordResetRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return redirect("usuarios:password_reset_verify")

        # Anti-spam: si hay un código muy reciente, reutilizar
        last_code = (
            PasswordResetCode.objects.filter(user=user, is_used=False)
            .order_by("-created_at")
            .first()
        )
        now = timezone.now()
        if last_code and (now - last_code.created_at).total_seconds() < 60 and not last_code.is_expired():
            code = last_code.code
            expires_at = last_code.expires_at
        else:
            code = _generate_code()
            expires_at = now + timedelta(minutes=10)
            PasswordResetCode.objects.create(
                user=user,
                code=code,
                expires_at=expires_at,
                requester_ip=request.META.get("REMOTE_ADDR"),
            )

        _send_reset_email(request, email, code)
        request.session["pr_email"] = email  # conveniencia
        return redirect("usuarios:password_reset_verify")

    return render(request, "usuarios/password_reset_request.html", {"form": form})


def password_reset_verify(request):
    """
    Paso 2: ingresar código de 6 dígitos.
    """
    # Permite prellenar por querystring (desde el correo)
    initial_email = request.GET.get("email") or request.session.get("pr_email", "")
    form = PasswordResetVerifyForm(request.POST or None, initial={"email": initial_email})

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        code = form.cleaned_data["code"].strip()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return redirect("usuarios:password_reset_verify")

        prc = (
            PasswordResetCode.objects.filter(user=user, code=code, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if not prc or prc.is_expired():
            return redirect("usuarios:password_reset_verify")

        if prc.attempts >= 5:
            return redirect("usuarios:password_reset_request")

        prc.attempts += 1
        prc.is_used = True
        prc.save(update_fields=["attempts", "is_used"])

        request.session["pr_email_verified"] = email
        request.session["pr_code"] = code
        return redirect("usuarios:password_reset_set")

    return render(request, "usuarios/password_reset_verify.html", {"form": form})


def password_reset_set(request):
    """
    Paso 3: elegir nueva contraseña (solo si ya verificó el código).
    Tras actualizarla, mostramos una pantalla de confirmación y redirigimos al login.
    """
    email = request.session.get("pr_email_verified")
    code = request.session.get("pr_code")
    if not email or not code:
        return redirect("usuarios:password_reset_request")

    form = PasswordResetSetForm(request.POST or None, initial={"email": email, "code": code})

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        code = form.cleaned_data["code"].strip()
        password = form.cleaned_data["password1"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return redirect("usuarios:password_reset_request")

        last_used = (
            PasswordResetCode.objects
            .filter(user=user, code=code, is_used=True, expires_at__gte=timezone.now() - timedelta(minutes=30))
            .order_by("-created_at")
            .first()
        )
        if not last_used:
            return redirect("usuarios:password_reset_request")

        user.set_password(password)
        user.save(update_fields=["password"])

        for k in ("pr_email", "pr_email_verified", "pr_code"):
            request.session.pop(k, None)

        return render(
            request,
            "usuarios/password_reset_done.html",
            {"redirect_url": "usuarios:login", "redirect_delay_ms": 3000},
        )

    return render(request, "usuarios/password_reset_set.html", {"form": form})
