from django.utils import timezone
from decimal import Decimal

from apps.sii.services.client import get_provider
from apps.sii.models import SIITransaccion
from apps.sii.utils import resolve_empresa_for_request

# Si cambias el import del modelo, ajusta esta ruta
from apps.documentos.models import Documento

def _dec_to_int_safe(value):
    if value is None:
        return None
    # total al SII suele ir sin decimales; ajusta si tu caso requiere decimales
    return int(Decimal(value))

def validar_documento_con_sii(request, documento: Documento) -> dict:
    """
    Construye el payload a partir del Documento y llama a validar_dte.
    Actualiza campos sii_* en el Documento y registra la transacción.
    """
    prov = get_provider()
    empresa = resolve_empresa_for_request(request)  # empresa activa por membresía o ?empresa_rut=

    # Mapeo básico de tipo_documento → código SII
    tipo_map = {
        "factura_afecta": 33,
        "factura_exenta": 34,
        "boleta_afecta": 39,
        "boleta_exenta": 41,
        "nota_credito": 61,
    }
    tipo_dte = tipo_map.get(documento.tipo_documento, 33)

    payload = {
        "emisor_rut": empresa.rut if empresa else "",        # tu empresa/emisor
        "receptor_rut": documento.rut_proveedor or "",       # proveedor (receptor en tu modelo actual)
        "tipo_dte": tipo_dte,
        "folio": int(documento.folio or 0) if (documento.folio or "").isdigit() else 0,
        "monto_total": _dec_to_int_safe(documento.total) or 0,
        "fecha_emision": documento.fecha_emision.isoformat() if documento.fecha_emision else timezone.now().date().isoformat(),
        "ted": "<TED>MOCK</TED>",   # en mock no exigimos el contenido real
    }

    res = prov.validar_dte(**payload)

    # Actualizar documento
    documento.sii_track_id = res.get("track_id") or ""
    documento.sii_estado = "ACEPTADO" if res.get("ok") else "RECHAZADO"
    documento.sii_glosa = res.get("glosa", "")
    documento.validado_sii = bool(res.get("ok"))  # si quieres marcar True solo cuando ACEPTADO
    documento.sii_validado_en = timezone.now()
    documento.save(update_fields=[
        "sii_track_id", "sii_estado", "sii_glosa", "validado_sii", "sii_validado_en"
    ])

    # Traza
    SIITransaccion.objects.create(
        empresa=empresa,
        endpoint="validar_dte",
        track_id=documento.sii_track_id or None,
        request_payload=payload,
        response_payload=res,
        ok=bool(res.get("ok", False)),
        status_code=200 if res.get("ok") else 202,
        estado=("ACEPTADO" if res.get("ok") else "RECHAZADO"),
    )

    return res

def refrescar_estado_sii(request, documento: Documento) -> dict:
    """
    Consulta estado por track_id y actualiza el Documento.
    """
    empresa = resolve_empresa_for_request(request)
    prov = get_provider()
    track = documento.sii_track_id
    if not track:
        return {"ok": False, "detail": "Documento no tiene track_id en SII"}

    res = prov.estado_dte(track)

    documento.sii_estado = res.get("estado", "") or documento.sii_estado
    documento.sii_glosa = res.get("glosa", "") or documento.sii_glosa
    documento.save(update_fields=["sii_estado", "sii_glosa"])

    SIITransaccion.objects.create(
        empresa=empresa,
        endpoint="estado_dte",
        track_id=track,
        request_payload={"track_id": track, "documento_id": documento.id},
        response_payload=res,
        ok=(res.get("estado") == "ACEPTADO"),
        status_code=200,
        estado=res.get("estado"),
    )
    return res

def refrescar_estado_sii_system(documento):
    """
    Variante para Celery (sin request). Usa la empresa del Documento.
    """
    prov = get_provider()
    track = documento.sii_track_id
    if not track:
        return {"ok": False, "detail": "Documento no tiene track_id en SII"}

    res = prov.estado_dte(track)

    # Actualiza documento
    old_estado = documento.sii_estado or ""
    documento.sii_estado = res.get("estado", "") or documento.sii_estado
    documento.sii_glosa = res.get("glosa", "") or documento.sii_glosa
    documento.save(update_fields=["sii_estado", "sii_glosa"])

    # Trazabilidad (empresa viene desde el documento)
    SIITransaccion.objects.create(
        empresa=documento.empresa if hasattr(documento, "empresa") else None,
        endpoint="estado_dte",
        track_id=track,
        request_payload={"track_id": track, "documento_id": documento.id, "system": True},
        response_payload=res,
        ok=(res.get("estado") == "ACEPTADO"),
        status_code=200,
        estado=res.get("estado"),
    )
    return res