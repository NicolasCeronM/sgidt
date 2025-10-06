from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# 👇 añade este import
from rest_framework.authentication import BaseAuthentication

from .serializers import LoginSerializer, UserSerializer, empresas_de_usuario

class NoAuth(BaseAuthentication):
    def authenticate(self, request):
        return None

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    # 👇 esto evita que DRF aplique SessionAuthentication (y por ende CSRF)
    authentication_classes = [NoAuth]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
                "empresas": empresas_de_usuario(user),
            },
            status=status.HTTP_200_OK,
        )

class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # 👇 aquí sí usamos la auth por defecto (JWT/Session) que definiste en settings
    # (no declares authentication_classes y hereda de settings)
    def get(self, request):
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "empresas": empresas_de_usuario(request.user),
            },
            status=status.HTTP_200_OK,
        )
