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
from .models import DropboxCredential
from dropbox import Dropbox, DropboxOAuth2Flow
import time
from dropbox.exceptions import ApiError


# A dónde volver siempre (ajusta si usas namespace: p.ej. "panel:configuraciones")
REDIRECT_NAME = "panel:configuraciones"

# ----- Google Integration -------#
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

        #messages.success(request, "Google Drive conectado correctamente.")
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
    #messages.info(request, "Google Drive desconectado.")
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



# ----- Dropbox Integration -------#
def _flow_dropbox(request):
    scopes = getattr(settings, "DROPBOX_SCOPES", [
        "files.metadata.read", "files.content.read", "files.content.write"
    ])

    return DropboxOAuth2Flow(
        consumer_key=settings.DROPBOX_APP_KEY,
        consumer_secret=settings.DROPBOX_APP_SECRET,
        redirect_uri=settings.DROPBOX_REDIRECT_URI,
        session=request.session,
        csrf_token_session_key="dropbox_auth_csrf",
        token_access_type="offline",
        scope=scopes, 
    )

@login_required
def dropbox_connect(request):
    return redirect(_flow_dropbox(request).start())

@login_required
def dropbox_callback(request):
    try:
        result = _flow_dropbox(request).finish(request.GET)
        data = {
            "refresh_token": getattr(result, "refresh_token", None),
            "access_token":  getattr(result, "access_token", None),
            "expires_at":    int(time.time()) + 4*60*60,
            "account_id":    getattr(result, "account_id", None),
        }
        if not data["refresh_token"]:
            messages.error(request, "Dropbox no entregó refresh_token. Revisa permisos/offline access.")
            return redirect(REDIRECT_NAME)

        DropboxCredential.objects.update_or_create(
            user=request.user, defaults={"credentials": data}
        )
        #messages.success(request, "Dropbox conectado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al conectar Dropbox: {e}")
    return redirect(REDIRECT_NAME)

@login_required
def dropbox_disconnect(request):
    DropboxCredential.objects.filter(user=request.user).delete()
    #messages.info(request, "Dropbox desconectado.")
    return redirect(REDIRECT_NAME)

@login_required
def dropbox_files(request):
    cred = DropboxCredential.objects.filter(user=request.user).first()
    if not cred:
        messages.error(request, "Conecta Dropbox primero.")
        return redirect("panel:configuraciones")

    dbx = Dropbox(
        app_key=settings.DROPBOX_APP_KEY,
        app_secret=settings.DROPBOX_APP_SECRET,
        oauth2_refresh_token=cred.credentials.get("refresh_token"),
    )

    try:
        res = dbx.files_list_folder(path="")  # raíz; ajusta si navegas por carpetas

        files = []
        for e in res.entries:
            tag = getattr(e, ".tag", "file")
            is_folder = (tag == "folder")

            client_mod = getattr(e, "client_modified", None)
            server_mod = getattr(e, "server_modified", None)

            link = None
            if not is_folder:
                try:
                    # 1) ¿Ya existe un shared link directo para esta ruta?
                    existing = dbx.sharing_list_shared_links(
                        path=e.path_lower, direct_only=True
                    ).links
                    if existing:
                        link = existing[0].url
                    else:
                        # 2) Créalo si no existe
                        link = dbx.sharing_create_shared_link_with_settings(
                            e.path_lower
                        ).url

                    # Opcional: forzar descarga directa
                    if link:
                        link = link.replace("?dl=0", "?dl=1")
                        # o: link = link.replace("?dl=0","?raw=1") para vista en navegador
                except ApiError:
                    # Falta scope de sharing o política del equipo no permite crear links
                    link = None

            files.append({
                "name": e.name,
                "id": getattr(e, "id", None),
                "tag": tag,                       # "file" | "folder"
                "is_folder": is_folder,
                "path": getattr(e, "path_lower", None) or getattr(e, "path_display", None),
                "client_modified": client_mod.isoformat() if client_mod else None,
                "server_modified": server_mod.isoformat() if server_mod else None,
                "link": link,
            })

        return render(request, "integraciones/dropbox_files.html", {"files": files})

    except Exception as e:
        return render(
            request,
            "integraciones/dropbox_files.html",
            {"error": f"Error listando archivos: {e}"}
        )