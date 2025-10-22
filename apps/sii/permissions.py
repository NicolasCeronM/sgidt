# apps/sii/permissions.py
from rest_framework.permissions import IsAuthenticated

class IsAuthenticatedCompany(IsAuthenticated):
    pass  # hook para extender en el futuro si necesitas scoping extra
