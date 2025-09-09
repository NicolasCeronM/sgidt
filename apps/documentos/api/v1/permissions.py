# apps/documentos/api/v1/permissions.py
from rest_framework.permissions import BasePermission
from apps.empresas.models import EmpresaUsuario
from ...models import Documento

class IsCompanyMember(BasePermission):
    def has_permission(self, request, view):
        return EmpresaUsuario.objects.filter(usuario=request.user).exists()

    def has_object_permission(self, request, view, obj: Documento):
        return EmpresaUsuario.objects.filter(usuario=request.user, empresa=obj.empresa).exists()
