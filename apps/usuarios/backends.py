# backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import re

UserModel = get_user_model()

def _norm_rut(texto: str) -> str:
    # quita puntos y guion, mayúscula para K
    return re.sub(r"[.\-]", "", (texto or "").strip()).upper()

class EmailRutOrUsernameBackend(ModelBackend):
    """
    Permite login con email, RUT o username usando el campo 'username' del form.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        user = None

        # 1) email (case-insensitive)
        if user is None:
            try:
                user = UserModel.objects.get(email__iexact=username)
            except UserModel.DoesNotExist:
                user = None

        # 2) RUT (normalizado)
        if user is None:
            norm_in = _norm_rut(username)
            # Trae un candidato y compara normalizado en Python
            candidato = UserModel.objects.filter(rut__iexact=username).first() or \
                        UserModel.objects.filter(rut__iendswith=norm_in[-5:]).first()  # heurística
            if candidato and _norm_rut(candidato.rut) == norm_in:
                user = candidato

        # 3) username (compatibilidad)
        if user is None:
            try:
                user = UserModel.objects.get(username__iexact=username)
            except UserModel.DoesNotExist:
                user = None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
