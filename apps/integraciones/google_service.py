from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime

def _parse_expiry(value):
    """Convierte expiry a datetime o None (acepta ISO con 'Z' u offset)."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        v = value
        # '2025-08-26T01:55:00Z' -> '2025-08-26T01:55:00+00:00'
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(v)
        except Exception:
            return None
    return None

def credentials_from_json(data: dict) -> Credentials:
    return Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=list(data.get("scopes", settings.GOOGLE_SCOPES)),
        expiry=_parse_expiry(data.get("expiry")),  # ← aquí el parse
    )

def to_json(creds: Credentials) -> dict:
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "scopes": list(getattr(creds, "scopes", settings.GOOGLE_SCOPES)),
        "expiry": creds.expiry.isoformat() if getattr(creds, "expiry", None) else None,
    }

def build_drive_service(creds_json: dict):
    creds = credentials_from_json(creds_json)
    return build("drive", "v3", credentials=creds, cache_discovery=False)
