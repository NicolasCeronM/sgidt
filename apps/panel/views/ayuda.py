# apps/panel/views/help.py
import json, os, re
from difflib import SequenceMatcher
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib import messages
from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from weasyprint import HTML, CSS

from ..forms import HelpContactForm

class HelpView(TemplateView):
    template_name = "panel/ayuda.html"

class FAQView(TemplateView):
    template_name = "panel/faq.html"

class StatusView(TemplateView):
    template_name = "panel/estado.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["services"] = [
            {"name": "API SGIDT", "status": "operational", "note": "Sin incidentes"},
            {"name": "Google Drive", "status": "degraded", "note": "Latencias intermitentes"},
            {"name": "Dropbox", "status": "operational", "note": "OK"},
            {"name": "Correo saliente", "status": "maintenance", "note": "Ventana 00:30–01:00"},
        ]
        ctx["last_updated"] = "Actualizado hace 2 min (placeholder)"
        return ctx

@require_POST
@csrf_protect
def help_contact(request):
    form = HelpContactForm(request.POST)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not form.is_valid():
        if is_ajax:
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        messages.error(request, "Revisa los campos del formulario.")
        return redirect(reverse("panel:ayuda"))

    # Email render
    context = {
        "name": form.cleaned_data["name"],
        "email": form.cleaned_data["email"],
        "message": form.cleaned_data["message"],
    }
    text_content = render_to_string("correo/ayuda_contacto.txt", context)
    html_content = render_to_string("correo/ayuda_contacto.html", context)

    subject = f"[SGIDT] Contacto de ayuda - {context['name']}"
    to = [getattr(settings, "SUPPORT_EMAIL", "sgidtchile@gmail.com")]

    email_msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=to,
        reply_to=[context["email"]],
    )
    email_msg.attach_alternative(html_content, "text/html")
    email_msg.send()

    if is_ajax:
        return JsonResponse({"ok": True})

    messages.success(request, "Tu mensaje fue enviado. Te contactaremos pronto.")
    return redirect(reverse("panel:ayuda"))

# ==== Chatbot soporte (mismo contenido que tenías, solo movido) ====
_ACCENTS = str.maketrans("áéíóúñüÁÉÍÓÚÑÜ", "aeiounuAEIOUNU")
def _norm(s: str) -> str:
    s = (s or "").strip()
    s = s.translate(_ACCENTS).lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s

def _tokens(s: str):
    return set(t for t in _norm(s).split() if len(t) > 2)

def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    uni = len(ta | tb)
    return inter / uni

def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()

def _score(a: str, b: str) -> float:
    return 0.6 * _jaccard(a, b) + 0.4 * _ratio(a, b)

_KB = []
_ERRORS = []
_KB_PATH = os.path.join(settings.BASE_DIR, "static", "ayuda", "kb", "faq_kb.json")
_ERRORS_PATH = os.path.join(settings.BASE_DIR, "static", "ayuda", "kb", "errors_kb.json")
if os.path.exists(_KB_PATH):
    try:
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            _KB = json.load(f)
    except Exception:
        _KB = []
if os.path.exists(_ERRORS_PATH):
    try:
        with open(_ERRORS_PATH, "r", encoding="utf-8") as f:
            _ERRORS = json.load(f)
    except Exception:
        _ERRORS = []

SYN = {
    "drive": {"google drive", "gdrive", "drive", "google"},
    "dropbox": {"dropbox"},
    "empresa": {"empresa", "razon social", "rut", "datos empresa", "correo empresa", "ajustes"},
    "backup": {"respaldo", "backup", "copia", "frecuencia"},
    "subir": {"subir", "cargar", "upload", "pdf", "archivo"},
    "sii": {"sii", "validacion", "simpleapi"},
    "roles": {"roles", "permisos", "accesos", "usuarios"},
    "seguridad": {"seguridad", "contrasena", "clave", "password"},
    "manual": {"manual", "documentacion", "ayuda pdf"},
    "contacto": {"contacto", "soporte", "correo"},
    "nav": {"navegacion", "menu", "donde encuentro", "no encuentro"}
}
RULES = [
    ("drive", "Ve a **Configuración → Integraciones** y presiona **Conectar Google Drive**. Autoriza y vuelve a SGIDT."),
    ("dropbox", "En **Configuración → Integraciones**, elige **Dropbox → Conectar** y completa la autorización."),
    ("empresa", "Ve a **Configuración → Ajustes de la Empresa**. Completa los campos y presiona **Guardar**."),
    ("backup", "En **Ajustes de la Empresa**, define **Respaldo Automático** (Diario/Semanal/Mensual) y guarda."),
    ("subir", "En **Documentos**, pulsa **Subir** y elige tu PDF (ideal < **10MB**). Evita caracteres especiales en el nombre."),
    ("sii", "En **Validación SII**, carga el XML/JSON del DTE, ejecuta la validación y revisa resultados."),
    ("roles", "La gestión de usuarios y permisos está en **Configuración** del administrador."),
    ("seguridad", "Usa **¿Olvidaste tu contraseña?** en el login o cámbiala desde tu perfil si estás autenticado."),
    ("manual", "Descarga el **Manual de Usuario** desde **Ayuda → Manual de Usuario**."),
    ("contacto", "Puedes escribir en este chat, usar **Contacto Rápido** o enviar un correo a **soporte@sgidt.cl**."),
    ("nav", "Los módulos están en la barra lateral: **Dashboard**, **Documentos**, **Proveedores**, **Reportes**, **Validación SII** y **Configuración**.")
]
SMALL_TALK = [
    (r"^(hola|buenas|que tal|holi)\b", "¡Hola! 👋 ¿En qué puedo ayudarte?"),
    (r"(gracias|muchas gracias|te agradezco)$", "¡Con gusto! ¿Necesitas algo más?"),
    (r"(adios|hasta luego|nos vemos)$", "¡Hasta luego! Si surge algo, aquí estaré.")
]

def _suggest_from_query(qn: str, k: int = 4):
    toks = _tokens(qn)
    scored = []
    for s in ["Conectar Google Drive","Conectar Dropbox","Cambiar datos de la empresa","Respaldo Automático","Subir un PDF","Validación con SII","Descargar Manual"]:
        sc = _score(qn, s)
        if any(t in _norm(s) for t in toks): sc += 0.1
        scored.append((sc, s))
    scored.sort(reverse=True)
    return [s for _, s in scored[:k]]

@require_POST
@csrf_protect
def chatbot_ask(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"reply": "No entendí tu mensaje. ¿Puedes reformularlo?"}, status=400)

    q = (payload.get("message") or "").strip()
    if not q:
        return JsonResponse({
            "reply": "¿En qué puedo ayudarte? Ejemplos: **Conectar Google Drive**, **Subir un PDF**, **Cambiar datos de la empresa**.",
            "suggest": _suggest_from_query("")
        })

    # 1) small talk
    for pat, ans in SMALL_TALK:
        if re.search(pat, _norm(q)):
            return JsonResponse({"reply": ans, "suggest": _suggest_from_query(q)})

    # 2) errores por patrones
    qn = _norm(q)
    for e in _ERRORS:
        for pat in e.get("patrones", []):
            try:
                if re.search(pat, q, flags=re.I) or pat.lower() in qn:
                    pasos_md = "\n".join([f"- {p}" for p in e.get("pasos", [])])
                    reply = f"**{e.get('titulo','Ocurrió un inconveniente.')}**\n\n{pasos_md}"
                    nota = e.get("nota")
                    if nota: reply += f"\n\n**Nota:** {nota}"
                    request.session["chat_ctx"] = {"last_topic": f"error:{e.get('nombre','general')}", "ts": timezone.now().isoformat()}
                    return JsonResponse({"reply": reply, "suggest": _suggest_from_query(q)})
            except re.error:
                if pat.lower() in qn:
                    pasos_md = "\n".join([f"- {p}" for p in e.get("pasos", [])])
                    reply = f"**{e.get('titulo','Ocurrió un inconveniente.')}**\n\n{pasos_md}"
                    nota = e.get("nota")
                    if nota: reply += f"\n\n**Nota:** {nota}"
                    request.session["chat_ctx"] = {"last_topic": f"error:{e.get('nombre','general')}", "ts": timezone.now().isoformat()}
                    return JsonResponse({"reply": reply, "suggest": _suggest_from_query(q)})

    # 3) reglas por intención
    for key, ans in RULES:
        if any(word in qn for word in SYN.get(key, [])):
            request.session["chat_ctx"] = {"last_topic": key, "ts": timezone.now().isoformat()}
            return JsonResponse({"reply": ans, "suggest": _suggest_from_query(q)})

    # 4) búsqueda difusa en KB
    best = (0.0, None)
    def _score(q,a):
        return 0.6*len(set(_norm(q).split()) & set(_norm(a).split()))/max(1,len(set(_norm(q).split()) | set(_norm(a).split()))) + 0.4*SequenceMatcher(None,_norm(q),_norm(a)).ratio()
    for item in _KB:
        for cand in item.get("q", []):
            s = _score(q, cand)
            if s > best[0]:
                best = (s, item.get("a"))
    if best[1] and best[0] >= 0.28:
        request.session["chat_ctx"] = {"last_topic": "kb", "ts": timezone.now().isoformat()}
        return JsonResponse({"reply": best[1], "suggest": _suggest_from_query(q)})

    # 5) fallback
    reply = ("No tengo una respuesta exacta todavía, pero puedo ayudarte con **integraciones**, "
             "**ajustes de la empresa**, **carga de documentos** y **validación SII**. "
             "¿Puedes darme un poco más de contexto?")
    return JsonResponse({"reply": reply, "suggest": _suggest_from_query(q)})

# ===========================
#   PDF: Manual de Usuario
# ===========================
def manual_usuario_pdf(request):
    """
    Genera y descarga el Manual de Usuario en PDF
    a partir de la plantilla templates/manual/manual_usuario.html
    y el CSS de impresión en static/manual/css/manual_print.css
    """
    secciones = [
        {
            "id": "introduccion",
            "titulo": "Introducción",
            "html": """
                <p><strong>SGIDT</strong> es un sistema de gestión inteligente tributario para pymes chilenas.
                Este manual explica la navegación, los módulos y ejemplos de uso paso a paso.</p>
            """,
        },
        {
            "id": "cuentas",
            "titulo": "Cuentas de Usuario y Acceso",
            "html": """
                <ul>
                    <li>Registro, inicio de sesión y recuperación de contraseña.</li>
                    <li>Gestión de perfil y permisos.</li>
                </ul>
            """,
        },
        {
            "id": "validaciones",
            "titulo": "Validaciones con SII (SimpleAPI)",
            "html": """
                <p>Cómo subir XML/JSON de DTE, lanzar la validación y leer los resultados.
                Recomendaciones para errores frecuentes.</p>
            """,
        },
        {
            "id": "integraciones",
            "titulo": "Integraciones: Google Drive y Dropbox",
            "html": """
                <p>Conectar cuentas, otorgar permisos, persistencia de tokens y explorar/descargar archivos.</p>
            """,
        },
        {
            "id": "panel_estado",
            "titulo": "Centro de Estado",
            "html": """
                <p>Monitoreo de servicios, integraciones y disponibilidad del sistema.</p>
            """,
        },
        {
            "id": "soporte",
            "titulo": "Soporte y Contacto",
            "html": """
                <p>Flujo para reportar incidencias desde Ayuda → Contacto Rápido y buenas prácticas.</p>
            """,
        },
    ]

    context = {
        "titulo": "SGIDT · Manual de Usuario",
        "version": "v1.0",
        "empresa": "SGIDT",
        "secciones": secciones,
    }

    html_string = render_to_string("manual/manual_usuario.html", context)

    css_fs = os.path.join(settings.BASE_DIR, "static", "manual", "css", "manual_print.css")
    stylesheets = [CSS(filename=css_fs)] if os.path.exists(css_fs) else []

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(
        stylesheets=stylesheets
    )

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="sgidt-manual.pdf"'
    return response