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
        fields = ["id","rut", "email","tipo_contribuyente", "first_name", "last_name", "is_active","foto"]

def empresas_de_usuario(user: User):
    qs = EmpresaUsuario.objects.select_related("empresa").filter(usuario=user)
    return [
        {
         "empresa_id": m.empresa_id, 
         "empresa_nombre": m.empresa.razon_social, 
         "giro":m.empresa.giro,
         #"logo_empresa": m.empresa.logo,
         "rol": m.rol,
         "emailContacto":m.empresa.email,
         "telefono":m.empresa.telefono,
         "direccion":m.empresa.direccion,
         "comuna":m.empresa.comuna,
         "region":m.empresa.region,
         }
        for m in qs
    ]
