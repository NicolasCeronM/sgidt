from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Documento
from apps.sii.tasks import check_and_kickoff_sii  # la definimos abajo

REQUIRED_FIELDS = ("rut_proveedor", "folio", "total", "fecha_emision", "tipo_documento")

def _has_required_fields(doc: Documento) -> bool:
    return all([
        bool(getattr(doc, "rut_proveedor", None)),
        bool(getattr(doc, "folio", None)),
        bool(getattr(doc, "total", None)),
        bool(getattr(doc, "fecha_emision", None)),
        bool(getattr(doc, "tipo_documento", None)),
    ])

@receiver(post_save, sender=Documento)
def documento_post_save(sender, instance: Documento, created: bool, **kwargs):
    """
    - Al crear: marcar EN_PROCESO para SII y encolar un checker que arranca la validación
      apenas el doc tenga los campos mínimos (tras OCR).
    - Al actualizar: si el OCR acaba de completar campos y aún no hay track, dispara checker.
    """
    # Si ya tiene track o estado terminal, no hacemos nada
    if (instance.sii_track_id or "") or (instance.sii_estado or "") in {"ACEPTADO","RECHAZADO"}:
        return

    # setear EN_PROCESO visible en UI (si no estaba)
    if (instance.sii_estado or "") != "EN_PROCESO":
        instance.sii_estado = "EN_PROCESO"
        instance.validado_sii = False
        try:
            instance.save(update_fields=["sii_estado","validado_sii"])
        except Exception:
            # si estamos dentro de una transacción de creación, dejamos que continue
            pass

    # Si no están los campos aún, programamos checker; si ya están, también (arranca altiro)
    try:
        check_and_kickoff_sii.delay(instance.id)
    except Exception:
        # si no hay worker levantado, al menos intentamos ejecutarla async
        check_and_kickoff_sii.apply_async(args=[instance.id])
