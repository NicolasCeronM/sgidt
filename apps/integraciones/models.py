from django.conf import settings
from django.db import models

class GoogleDriveCredential(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="google_drive")
    credentials = models.JSONField()  # token, refresh_token, scopes, expiry...
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GoogleDriveCredential({self.user})"
