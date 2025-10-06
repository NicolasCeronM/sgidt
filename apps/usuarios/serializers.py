from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

# Si tu app de empresas usa otro path, ajusta este import:
from apps.empresas.models import EmpresaUsuario

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=attrs.get("username"),
            password=attrs.get("password"),
        )
        if not user:
            raise serializers.ValidationError("Credenciales inválidas.")
        if not user.is_active:
            raise serializers.ValidationError("Usuario deshabilitado.")
        attrs["user"] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active"]

def empresas_de_usuario(user: User):
    qs = EmpresaUsuario.objects.select_related("empresa").filter(usuario=user)
    return [
        {"empresa_id": m.empresa_id, "empresa_nombre": m.empresa.razon_social, "rol": m.rol}
        for m in qs
    ]
