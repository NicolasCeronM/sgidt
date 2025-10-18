from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.usuarios.models import PasswordResetCode
from .serializers import (
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    PasswordResetSetSerializer,
)
from apps.usuarios.views_password_reset import _generate_code, _send_reset_email

User = get_user_model()

class PasswordResetRequestAPIView(APIView):
    """
    Paso 1: Inicia el proceso de reseteo de contraseña.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email__iexact=email)
            code = _generate_code()
            
            # --- CORREGIDO: Calculamos y añadimos la fecha de expiración ---
            expires_at = timezone.now() + timedelta(minutes=15)
            PasswordResetCode.objects.create(user=user, code=code, expires_at=expires_at)
            # -------------------------------------------------------------
            
            _send_reset_email(request, email, code)
            
            return Response(
                {"detail": "Se ha enviado un código de verificación a tu correo."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "Si tu correo está en nuestros registros, recibirás un código."},
                status=status.HTTP_200_OK
            )

# (El resto de las vistas no necesitan cambios, ya que solo leen los datos)

class PasswordResetVerifyAPIView(APIView):
    """
    Paso 2: Verifica el código enviado por el usuario.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        
        # --- CORREGIDO: Usamos el campo 'expires_at' para validar ---
        reset_code = PasswordResetCode.objects.filter(
            user__email__iexact=email,
            code=code,
            is_used=False,
            expires_at__gte=timezone.now() # Verificamos que no haya expirado
        ).first()
        # ----------------------------------------------------------

        if reset_code:
            return Response({"detail": "Código verificado correctamente."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "El código es inválido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetSetAPIView(APIView):
    """
    Paso 3: Establece la nueva contraseña.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        password = serializer.validated_data['password']

        # --- CORREGIDO: Usamos el campo 'expires_at' para validar ---
        reset_code = PasswordResetCode.objects.filter(
            user__email__iexact=email,
            code=code,
            is_used=False,
            expires_at__gte=timezone.now()
        ).first()
        # ----------------------------------------------------------

        if not reset_code:
            return Response({"error": "El código es inválido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = reset_code.user
        user.set_password(password)
        user.save()
        
        reset_code.is_used = True
        reset_code.save()
        
        return Response({"detail": "Tu contraseña ha sido actualizada exitosamente."}, status=status.HTTP_200_OK)