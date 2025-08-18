from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Permite login con email o username. El parámetro 'username' del form
        será el email que ingrese el usuario.
        """
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        user = None
        # 1) intentar por email
        try:
            user = UserModel.objects.get(email__iexact=username)
        except UserModel.DoesNotExist:
            # 2) intentar por username (compatibilidad)
            try:
                user = UserModel.objects.get(username__iexact=username)
            except UserModel.DoesNotExist:
                return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
