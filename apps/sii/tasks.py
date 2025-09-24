from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.documentos.models import Documento
from apps.sii.models import SIITransaccion
from apps.sii.services.client import get_provider
from apps.sii.services.sii_integration import refrescar_estado_sii_system

REQUIRED_FIELDS = ("rut_proveedor", "folio", "total", "fecha_emision", "tipo_documento")

def _doc_ready(doc: Documento) -> bool:
    return all([
        bool(getattr(doc, "rut_proveedor", None)),
        bool(getattr(doc, "folio", None)),
        bool(getattr(doc, "total", None)),
        bool(getattr(doc, "fecha_emision", None)),
        bool(getattr(doc, "tipo_documento", None)),
    ])

def _dec_to_int(v):
    try: return int(Decimal(v or 0))
    except: return 0

@shared_task(bind=True, max_retries=0)
def check_and_kickoff_sii(self, documento_id: int, retries_left: int = 20, interval_sec: int = 15):
    """
    Espera activa a que el Documento tenga campos mínimos (OCR).
    - Reintenta cada `interval_sec` hasta `retries_left` veces (~5 min por defecto).
    - Cuando está listo: llama a start_sii_validation_core (sin request).
    """
    doc = Documento.objects.filter(pk=documento_id).first()
    if not doc:
        return {"ok": False, "detail": "document_not_found"}

    # si ya tiene track o estado final, salir
    if (doc.sii_track_id or "") or (doc.sii_estado or "") in {"ACEPTADO","RECHAZADO"}:
        return {"ok": True, "detail": "already_validated_or_has_track"}

    if not _doc_ready(doc):
        if retries_left <= 0:
            # no estuvo listo a tiempo: dejar en EN_PROCESO y terminar
            return {"ok": False, "detail": "not_ready_timeout"}
        # reintentar
        return check_and_kickoff_sii.apply_async(
            args=[documento_id, retries_left - 1, interval_sec],
            countdown=interval_sec
        )

    # Ya está listo → validar
    return start_sii_validation_core.apply_async(args=[documento_id]).id

@shared_task(bind=True)
def start_sii_validation_core(self, documento_id: int):
    """
    Valida el documento en SII (mock/real) y agenda refrescos escalonados si aplica.
    """
    from django.utils import timezone
    doc = Documento.objects.filter(pk=documento_id).first()
    if not doc:
        return {"ok": False, "detail": "document_not_found"}

    # map de tipo
    tipo_map = {"factura_afecta":33,"factura_exenta":34,"boleta_afecta":39,"boleta_exenta":41,"nota_credito":61}
    tipo_dte = tipo_map.get(doc.tipo_documento, 33)

    empresa = getattr(doc, "empresa", None)
    emisor_rut = getattr(empresa, "rut", "") or ""
    payload = {
        "emisor_rut": emisor_rut,
        "receptor_rut": doc.rut_proveedor or "",
        "tipo_dte": tipo_dte,
        "folio": int(doc.folio or 0) if str(doc.folio or "").isdigit() else 0,
        "monto_total": _dec_to_int(doc.total),
        "fecha_emision": (doc.fecha_emision or timezone.now().date()).isoformat(),
        "ted": "<TED>MOCK</TED>",
    }

    prov = get_provider()
    res = prov.validar_dte(**payload)

    doc.sii_track_id = res.get("track_id") or ""
    doc.sii_glosa = res.get("glosa","")
    doc.sii_estado = "ACEPTADO" if res.get("ok") else "RECHAZADO"
    doc.validado_sii = bool(res.get("ok"))
    doc.sii_validado_en = timezone.now()
    doc.save(update_fields=["sii_track_id","sii_glosa","sii_estado","validado_sii","sii_validado_en"])

    SIITransaccion.objects.create(
        empresa=empresa, endpoint="validar_dte",
        track_id=doc.sii_track_id or None, request_payload=payload,
        response_payload=res, ok=bool(res.get("ok")),
        status_code=200 if res.get("ok") else 202,
        estado=("ACEPTADO" if res.get("ok") else "RECHAZADO"),
    )

    # si no es terminal y hay track, agenda refrescos (10s, 30s, 2m, 5m)
    terminal = doc.sii_estado in {"ACEPTADO","RECHAZADO"}
    if doc.sii_track_id and not terminal:
        refresh_sii_estado_documento.apply_async(args=[doc.id], countdown=10)
        refresh_sii_estado_documento.apply_async(args=[doc.id], countdown=30)
        refresh_sii_estado_documento.apply_async(args=[doc.id], countdown=120)
        refresh_sii_estado_documento.apply_async(args=[doc.id], countdown=300)

    return {"ok": True, "track": doc.sii_track_id, "estado": doc.sii_estado}

@shared_task(bind=True, max_retries=0)
def refresh_sii_estado_documento(self, documento_id: int):
    doc = Documento.objects.filter(pk=documento_id).first()
    if not doc or not doc.sii_track_id:
        return {"ok": False, "detail": "no_doc_or_track"}
    res = refrescar_estado_sii_system(doc)
    return {"ok": True, "result": res}
