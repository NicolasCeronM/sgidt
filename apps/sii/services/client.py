# apps/sii/services/client.py
from django.conf import settings
from .providers import MockSIIProvider, RealSIIProvider, SIIProvider

def get_provider() -> SIIProvider:
    if getattr(settings, "SII_USE_MOCK", True):
        return MockSIIProvider()
    return RealSIIProvider()
