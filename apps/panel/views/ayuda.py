# apps/panel/views/ayuda.py
from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from weasyprint import CSS, HTML

# ==== IA (Groq) ==============================================================
try:
    from groq import Groq  # type: ignore
except Exception:  # biblioteca no instalada en algunos entornos
    Groq = None  # type: ignore

# =============================================================================
#   Vistas estáticas
# =============================================================================
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

# =============================================================================
#   Contacto rápido
# =============================================================================
@require_POST
@csrf_protect
def help_contact(request):
    # import local para evitar ciclos
    from ..forms import HelpContactForm

    form = HelpContactForm(request.POST)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not form.is_valid():
        if is_ajax:
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        messages.error(request, "Revisa los campos del formulario.")
        return redirect(reverse("panel:ayuda"))

    ctx = {
        "name": form.cleaned_data["name"],
        "email": form.cleaned_data["email"],
        "message": form.cleaned_data["message"],
    }
    text_content = render_to_string("correo/ayuda_contacto.txt", ctx)
    html_content = render_to_string("correo/ayuda_contacto.html", ctx)

    subject = f"[SGIDT] Contacto de ayuda - {ctx['name']}"
    to = [getattr(settings, "SUPPORT_EMAIL", "sgidtchile@gmail.com")]

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=to,
        reply_to=[ctx["email"]],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

    if is_ajax:
        return JsonResponse({"ok": True})

    messages.success(request, "Tu mensaje fue enviado. Te contactaremos pronto.")
    return redirect(reverse("panel:ayuda"))

# =============================================================================
#   Utilidades NLP
# =============================================================================

# --- Detección de intención SGIDT vs global ---
_SGIDT_TERMS = {
    "sgidt","sii","simpleapi","dte","factura","drive","google drive","gdrive",
    "dropbox","integraciones","validacion","validación","documentos","proveedores",
    "reportes","configuracion","configuración","empresa","respaldo","backup","roles","permisos"
}

def _is_sgidt_related(qn: str) -> bool:
    return any(term in qn for term in _SGIDT_TERMS)

_ACCENTS = str.maketrans("áéíóúñüÁÉÍÓÚÑÜ", "aeiounuAEIOUNU")

def _norm(s: str) -> str:
    s = (s or "").strip().translate(_ACCENTS).lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s

def _tokens(s: str) -> set:
    return {t for t in _norm(s).split() if len(t) > 2}

def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))

def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()

def _score(a: str, b: str) -> float:
    return 0.6 * _jaccard(a, b) + 0.4 * _ratio(a, b)

def _topk(q: str, candidates: List[str], k: int = 5) -> List[str]:
    scored = [(_score(q, c), c) for c in candidates]
    scored.sort(reverse=True, key=lambda x: x[0])
    return [c for _, c in scored[:k]]

# =============================================================================
#   KB & reglas locales
# =============================================================================
_KB: List[Dict] = []
_ERRORS: List[Dict] = []

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
    "nav": {"navegacion", "menu", "donde encuentro", "no encuentro"},
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
    ("nav", "Los módulos están en la barra lateral: **Dashboard**, **Documentos**, **Proveedores**, **Reportes**, **Validación SII** y **Configuración**."),
]

SMALL_TALK = [
    (r"^(hola|buenas|que tal|holi)\b", "¡Hola! 👋 ¿En qué puedo ayudarte?"),
    (r"(gracias|muchas gracias|te agradezco)$", "¡Con gusto! ¿Necesitas algo más?"),
    (r"(adios|hasta luego|nos vemos)$", "¡Hasta luego! Si surge algo, aquí estaré."),
]

def _suggest_from_query(qn: str, k: int = 4) -> List[str]:
    opciones = [
        "Conectar Google Drive",
        "Conectar Dropbox",
        "Cambiar datos de la empresa",
        "Respaldo Automático",
        "Subir un PDF",
        "Validación con SII",
        "Descargar Manual",
    ]
    if not qn:
        return opciones[:k]
    scored = []
    for s in opciones:
        sc = _score(qn, s)
        if any(t in _norm(s) for t in _tokens(qn)):
            sc += 0.1
        scored.append((sc, s))
    scored.sort(reverse=True)
    return [s for _, s in scored[:k]]

# =============================================================================
#   Cliente IA (Groq) + respuesta
# =============================================================================
def _get_groq_client() -> Optional["Groq"]:
    api_key = getattr(settings, "GROQ_API_KEY", None)
    if not api_key or Groq is None:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        return None

_SYSTEM_PROMPT = (
    "Eres el asistente de soporte de SGIDT. Responde SOLO a lo preguntado y de forma MUY breve.\n"
    "Reglas de estilo:\n"
    "- No uses encabezados (#).\n"
    "- Usa a lo más 3 bullets cortos (<= 14 palabras cada uno) o 1 línea si cabe.\n"
    "- Usa **negritas** solo para nombres de menús o acciones dentro de SGIDT.\n"
    "- Si la pregunta NO es de SGIDT (p.ej., hora/clima/chistes), responde en 1 línea sin contenido extra.\n"
    "- Si falta un dato clave, pide SOLO ese dato en 1 línea.\n"
    "Prohibido inventar endpoints o credenciales."
)

_GLOBAL_PROMPT = (
    "Eres un asistente general. Responde en español, con precisión y brevedad.\n"
    "Reglas:\n"
    "- 1–3 bullets o 1 solo párrafo breve.\n"
    "- No uses encabezados (#).\n"
    "- Si la pregunta requiere datos en tiempo real o navegación, dilo claramente.\n"
    "- Evita divagar; responde directo. Si es una opinión, aclara que es general."
)


def _post_ai(text: str) -> str:
    """Limpia y recorta la salida de la IA."""
    if not text:
        return ""
    # Quita encabezados markdown
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    # Convierte bullets con '*' a '-'
    text = re.sub(r"(?m)^\s*\*\s+", "- ", text)
    # Limita a 3 viñetas y 120 palabras totales
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullets = [ln for ln in lines if ln.startswith("- ")]
    if bullets:
        bullets = bullets[:3]
        others = [ln for ln in lines if not ln.startswith("- ")]
        lines = others[:1] + bullets  # una línea + 3 bullets máximo
    text = "\n".join(lines)
    words = text.split()
    if len(words) > 120:
        text = " ".join(words[:120]) + "…"
    return text

def _ai_answer(query: str, context_snippets: List[str]) -> str:
    """Consulta Groq y devuelve respuesta breve y limpia."""
    client = _get_groq_client()
    if client is None:
        return (
            "No tengo acceso al motor de IA ahora mismo. "
            "Puedo ayudarte con **integraciones**, **ajustes de la empresa**, "
            "**carga de documentos** y **validación SII**. ¿Puedes darme más contexto?"
        )

    ctx = "\n\n".join(f"- {s.strip()}"[:600] for s in context_snippets)[:2000]
    try:
        resp = client.chat.completions.create(
            model=getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Pregunta: {query}\n\nContexto útil:\n{ctx}"},
            ],
            temperature=0.2,
            max_tokens=450,
        )
        raw = resp.choices[0].message.content.strip()
        return _post_ai(raw)
    except Exception:
        return (
            "Hubo un problema generando la respuesta con IA. "
            "Intenta otra vez o usa **Ayuda → Contacto Rápido**."
        )

def _ai_global_answer(query: str) -> str:
    client = _get_groq_client()
    if client is None:
        return "Puedo responder en general, pero ahora no tengo motor de IA disponible."
    try:
        resp = client.chat.completions.create(
            model=getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": _GLOBAL_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        raw = resp.choices[0].message.content.strip()
        return _post_ai(raw)  # reutilizamos el limpiador: sin #, máx 3 bullets, etc.
    except Exception:
        return "No pude responder ahora. Intenta nuevamente en un momento."

# ==== Respuestas directas (hora/fecha) =======================================
_TIME_PAT = re.compile(r"\b(que\s+hora|qué\s+hora|hora\s+actual|hora\s+(es|esta))\b", re.I)
_FECHA_PAT = re.compile(r"\b(que\s+fecha|qué\s+fecha|fecha\s+de\s+hoy)\b", re.I)

def _one_line(s: str, max_chars: int = 180) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return (s[: max_chars - 1] + "…") if len(s) > max_chars else s

def _is_time_query(q: str) -> bool:
    return bool(_TIME_PAT.search(q))

def _is_date_query(q: str) -> bool:
    return bool(_FECHA_PAT.search(q))

# =============================================================================
#   Chatbot principal
# =============================================================================
@require_POST
@csrf_protect
def chatbot_ask(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"reply": "No entendí tu mensaje. ¿Puedes reformularlo?"}, status=400)

    q = (payload.get("message") or "").strip()
    if not q:
        return JsonResponse(
            {
                "reply": "¿En qué puedo ayudarte? Ejemplos: **Conectar Google Drive**, **Subir un PDF**, **Cambiar datos de la empresa**.",
                "suggest": _suggest_from_query(""),
            }
        )

    qn = _norm(q)

    # Respuestas directas fuera de SGIDT
    if _is_time_query(qn):
        now = timezone.localtime()
        return JsonResponse(
            {"reply": _one_line(f"Son las {now.strftime('%H:%M')} ({now.tzinfo})."), "suggest": _suggest_from_query("hora")}
        )

    if _is_date_query(qn):
        today = timezone.localtime()
        return JsonResponse(
            {"reply": _one_line(f"Hoy es {today.strftime('%d-%m-%Y')} ({today.tzinfo})."), "suggest": _suggest_from_query("fecha")}
        )

    # 1) Small talk
    for pat, ans in SMALL_TALK:
        if re.search(pat, qn):
            return JsonResponse({"reply": ans, "suggest": _suggest_from_query(q)})

    # 2) Errores por patrones
    for e in _ERRORS:
        for pat in e.get("patrones", []):
            try:
                if re.search(pat, q, flags=re.I) or pat.lower() in qn:
                    pasos_md = "\n".join([f"- {p}" for p in e.get("pasos", [])])
                    reply = f"**{e.get('titulo', 'Ocurrió un inconveniente.')}**\n\n{pasos_md}"
                    nota = e.get("nota")
                    if nota:
                        reply += f"\n\n**Nota:** {nota}"
                    request.session["chat_ctx"] = {
                        "last_topic": f"error:{e.get('nombre', 'general')}",
                        "ts": timezone.now().isoformat(),
                    }
                    return JsonResponse({"reply": reply, "suggest": _suggest_from_query(q)})
            except re.error:
                if pat.lower() in qn:
                    pasos_md = "\n".join([f"- {p}" for p in e.get("pasos", [])])
                    reply = f"**{e.get('titulo', 'Ocurrió un inconveniente.')}**\n\n{pasos_md}"
                    nota = e.get("nota")
                    if nota:
                        reply += f"\n\n**Nota:** {nota}"
                    request.session["chat_ctx"] = {
                        "last_topic": f"error:{e.get('nombre', 'general')}",
                        "ts": timezone.now().isoformat(),
                    }
                    return JsonResponse({"reply": reply, "suggest": _suggest_from_query(q)})

    # 3) Reglas por intención
    for key, ans in RULES:
        if any(word in qn for word in SYN.get(key, [])):
            request.session["chat_ctx"] = {"last_topic": key, "ts": timezone.now().isoformat()}
            return JsonResponse({"reply": ans, "suggest": _suggest_from_query(q)})

    # 4) Búsqueda difusa en KB
    best = (0.0, None)

    def _local_score(qs: str, as_: str) -> float:
        return (
            0.6
            * len(set(_norm(qs).split()) & set(_norm(as_).split()))
            / max(1, len(set(_norm(qs).split()) | set(_norm(as_).split())))
            + 0.4 * SequenceMatcher(None, _norm(qs), _norm(as_)).ratio()
        )

    for item in _KB:
        for cand in item.get("q", []):
            s = _local_score(q, cand)
            if s > best[0]:
                best = (s, item.get("a"))

    if best[1] and best[0] >= 0.28:
        request.session["chat_ctx"] = {"last_topic": "kb", "ts": timezone.now().isoformat()}
        return JsonResponse({"reply": best[1], "suggest": _suggest_from_query(q)})
    if not _is_sgidt_related(qn):
        reply = _ai_global_answer(q)
        return JsonResponse({"reply": reply, "suggest": _suggest_from_query(q)})

    # 5) Fallback → IA con grounding (RULES)
    rule_texts = [f"{k}: {a}" for k, a in RULES]
    reply = _ai_answer(q, rule_texts[:8])
    return JsonResponse({"reply": reply, "suggest": _suggest_from_query(q)})

# =============================================================================
#   PDF: Manual de Usuario
# =============================================================================
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

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(stylesheets=stylesheets)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="sgidt-manual.pdf"'
    return response
