from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

from .models import GoogleDriveCredential
from .google_service import build_drive_service, to_json, credentials_from_json
from django.shortcuts import render

# A dónde volver siempre (ajusta si usas namespace: p.ej. "panel:configuraciones")
REDIRECT_NAME = "configuraciones"


def _flow():
    """Crea el flow OAuth con los valores del settings."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )


# -------------------------
# Conectar (inicia OAuth)
# -------------------------
@login_required
def google_connect(request):
    flow = _flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["google_oauth_state"] = state
    return redirect(auth_url)


# -------------------------
# Callback de Google
# -------------------------
@login_required
def google_callback(request):
    # Error explícito devuelto por Google
    if "error" in request.GET:
        messages.error(request, f"Google devolvió un error: {request.GET.get('error')}")
        return redirect(REDIRECT_NAME)

    # Si no viene el ?code=... (cancelado o flujo incompleto)
    if "code" not in request.GET:
        messages.error(request, "No se recibió el código de autorización. Intenta conectar nuevamente y acepta los permisos.")
        return redirect(REDIRECT_NAME)

    try:
        flow = _flow()
        # Intercambia el code por tokens
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        creds: Credentials = flow.credentials

        # Refresca si fuese necesario (no suele ocurrir en el primer canje)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        data = to_json(creds)
        if not data.get("token") and not data.get("refresh_token"):
            messages.error(request, "No se obtuvieron credenciales válidas desde Google.")
            return redirect(REDIRECT_NAME)

        # Guarda/actualiza las credenciales del usuario
        GoogleDriveCredential.objects.update_or_create(
            user=request.user,
            defaults={"credentials": data},
        )

        messages.success(request, "Google Drive conectado correctamente.")
        return redirect(REDIRECT_NAME)

    except HttpError as e:
        messages.error(request, f"Error de Google API: {e}")
    except Exception as e:
        messages.error(request, f"Ocurrió un error durante la conexión: {e}")

    return redirect(REDIRECT_NAME)


# -------------------------
# Desconectar
# -------------------------
@login_required
def google_disconnect(request):
    GoogleDriveCredential.objects.filter(user=request.user).delete()
    messages.info(request, "Google Drive desconectado.")
    return redirect(REDIRECT_NAME)


# -------------------------------------------------------
# (Compat) Ruta antigua /integraciones/google/files/
# -> ahora solo redirige a Configuraciones
# -------------------------------------------------------
@login_required
def google_list_files(request):
    return redirect(REDIRECT_NAME)


# -------------------------
# Demo de subida de archivo
# -------------------------
@login_required
def google_upload_demo(request):
    import io
    from googleapiclient.http import MediaIoBaseUpload

    cred = GoogleDriveCredential.objects.filter(user=request.user).first()
    if not cred:
        messages.error(request, "Conecta Google Drive primero.")
        return redirect(REDIRECT_NAME)

    try:
        service = build_drive_service(cred.credentials)
        content = io.BytesIO(b"Hola SGIDT desde Google Drive API!")
        media = MediaIoBaseUpload(content, mimetype="text/plain", resumable=False)
        file = service.files().create(
            body={"name": "sgidt_demo.txt"},
            media_body=media,
            fields="id,webViewLink"
        ).execute()
        messages.success(request, f"Archivo subido. Ver: {file.get('webViewLink')}")
    except HttpError as e:
        messages.error(request, f"Error al subir: {e}")
    except Exception as e:
        messages.error(request, f"Ocurrió un error: {e}")

    return redirect(REDIRECT_NAME)


@login_required
def google_files(request):
    cred = GoogleDriveCredential.objects.filter(user=request.user).first()
    if not cred:
        return redirect(REDIRECT_NAME)

    files, error = [], None
    try:
        creds = credentials_from_json(cred.credentials)
        if not creds.valid and creds.refresh_token:
            creds.refresh(Request())
            cred.credentials = to_json(creds)
            cred.save(update_fields=["credentials", "updated_at"])

        service = build_drive_service(cred.credentials)
        res = service.files().list(
            pageSize=50,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
        ).execute()
        files = res.get("files", [])
    except Exception as e:
        error = str(e)

    return render(request, "integraciones/google_files.html", {"files": files, "error": error})
