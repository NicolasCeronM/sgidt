from django.conf import settings
from django.db import models


# --- Google Drive OAuth ---
class GoogleDriveCredential(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="google_drive")
    credentials = models.JSONField()  # token, refresh_token, scopes, expiry...
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GoogleDriveCredential({self.user})"
    

# --- Dropbox OAuth (DEV) ---
class DropboxCredential(models.Model):
    """
    Guarda credenciales OAuth de Dropbox por usuario.
    - credentials: JSON con refresh_token (y opcionalmente access_token, expires_at, etc.)
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True)
    credentials = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Credencial de Dropbox"
        verbose_name_plural = "Credenciales de Dropbox"

    def __str__(self):
        return f"DropboxCredential<{self.user_id}>"