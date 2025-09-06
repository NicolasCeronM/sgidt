from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_date
from django.db import IntegrityError, transaction
from datetime import date, datetime
from decimal import Decimal

from .models import Documento
from apps.empresas.models import Empresa, EmpresaUsuario
from apps.documentos import ocr
import os

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _empresa_ids_del_usuario(user):
    return EmpresaUsuario.objects.filter(usuario=user).values_list("empresa_id", flat=True)

def _to_jsonable(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, (date, datetime)): return obj.isoformat()
    if isinstance(obj, dict): return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list): return [_to_jsonable(x) for x in obj]
    if isinstance(obj, tuple): return tuple(_to_jsonable(x) for x in obj)
    if isinstance(obj, set): return [_to_jsonable(x) for x in obj]
    return obj

def _to_decimal(v):
    if v is None or v == "": return None
    try: return Decimal(str(v))
    except Exception: return None

# Map simplificado del frontend → modelo
def _map_tipo_simple_to_query(tipo_simple: str):
    if not tipo_simple: return {}
    tipo_simple = tipo_simple.lower()
    if tipo_simple == "factura":
        return {"tipo_documento__startswith": "factura_"}
    if tipo_simple == "boleta":
        return {"tipo_documento__startswith": "boleta_"}
    if tipo_simple in {"nc", "nota_credito"}:
        return {"tipo_documento": "nota_credito"}
    return {}

def _map_estado_simple_to_query(estado: str):
    if not estado: return {}
    estado = estado.lower()
    if estado in {"cola", "pendiente"}:
        return {"estado__in": ["pendiente", "procesando"]}
    if estado in {"procesado", "validado"}:
        return {"estado": "procesado"}
    if estado == "error":
        return {"estado": "error"}
    return {}

# -------------------------------------------------------------------
# Página HTML
# -------------------------------------------------------------------
@login_required
def documentos_page(request):
    return render(request, "panel/documentos.html")

# -------------------------------------------------------------------
# API: listar
# -------------------------------------------------------------------
@login_required
@require_GET
def documentos_list_api(request):
    empresa_ids = list(_empresa_ids_del_usuario(request.user))
    qs = Documento.objects.filter(empresa_id__in=empresa_ids).order_by("-creado_en")

    f_desde = request.GET.get("from") or request.GET.get("date_from") or request.GET.get("dateFrom")
    f_hasta = request.GET.get("to") or request.GET.get("date_to") or request.GET.get("dateTo")
    tipo_simple = request.GET.get("type") or request.GET.get("docType")
    estado_simple = request.GET.get("status") or request.GET.get("docStatus")

    fecha_desde = parse_date(f_desde) if f_desde else None
    if isinstance(fecha_desde, datetime): fecha_desde = fecha_desde.date()
    if isinstance(fecha_desde, date): qs = qs.filter(fecha_emision__gte=fecha_desde)

    fecha_hasta = parse_date(f_hasta) if f_hasta else None
    if isinstance(fecha_hasta, datetime): fecha_hasta = fecha_hasta.date()
    if isinstance(fecha_hasta, date): qs = qs.filter(fecha_emision__lte=fecha_hasta)

    qs = qs.filter(**_map_tipo_simple_to_query(tipo_simple))
    qs = qs.filter(**_map_estado_simple_to_query(estado_simple))

    data = []
    for d in qs[:200]:
        data.append({
            "id": d.id,
            "fecha": d.fecha_emision.isoformat() if d.fecha_emision else "",
            "tipo": d.tipo_documento,
            "folio": d.folio,
            "rut_emisor": d.rut_proveedor,
            "total": float(d.total) if d.total is not None else None,
            "estado": d.estado,
            "archivo": d.archivo.url if d.archivo else "",
        })
    return JsonResponse({"results": data})

# -------------------------------------------------------------------
# API: upload + OCR (MVP síncrono)
# -------------------------------------------------------------------
@login_required
@require_POST
def documentos_upload_api(request):
    # Empresa activa (si está en sesión y el usuario pertenece)
    empresa = None
    eid = request.session.get("empresa_activa_id")
    if eid and EmpresaUsuario.objects.filter(usuario=request.user, empresa_id=eid).exists():
        empresa = Empresa.objects.filter(id=eid).first()
    if not empresa:
        eu = EmpresaUsuario.objects.filter(usuario=request.user).select_related("empresa").first()
        if eu: empresa = eu.empresa
    if not empresa:
        return HttpResponseBadRequest("Debes crear primero una empresa o no tienes permisos en ninguna.")

    files = request.FILES.getlist("files[]") or request.FILES.getlist("files")
    if not files:
        return HttpResponseBadRequest("No se recibieron archivos")

    created = 0; skipped = 0; errors = []

    for f in files:
        try:
            with transaction.atomic():
                doc = Documento(
                    empresa=empresa,
                    subido_por=request.user,
                    archivo=f,
                    estado="procesando",
                )
                doc.save()  # calcula hash/mime/size/extension

                local_path = doc.archivo.path
                result = ocr.parse_file(local_path, doc.mime_type)

                # JSON crudo del OCR (serializable)
                doc.ocr_json = _to_jsonable(result)
                # Texto plano para búsqueda
                doc.texto_plano = (result.get("raw_text") or "").strip()

                # Campos principales
                doc.tipo_documento = result.get("tipo_documento", "desconocido") or "desconocido"
                doc.folio = (result.get("folio") or "").strip()

                # fecha_emision ya viene date si es desde parse_text; si viene iso string, parsea
                fe = result.get("fecha_emision")
                if isinstance(fe, str):
                    fe = parse_date(fe)
                doc.fecha_emision = fe

                doc.rut_proveedor = (result.get("rut_proveedor") or "").replace(".", "").upper()
                doc.razon_social_proveedor = (result.get("proveedor_nombre") or "").strip()

                doc.iva_tasa = _to_decimal(result.get("iva_tasa"))
                doc.monto_neto = _to_decimal(result.get("monto_neto"))
                doc.monto_exento = _to_decimal(result.get("monto_exento"))
                doc.iva = _to_decimal(result.get("iva"))
                doc.total = _to_decimal(result.get("total"))

                # Metadatos OCR
                doc.ocr_fuente = result.get("fuente_texto") or ""
                doc.ocr_lang = os.getenv("TESSERACT_LANG", "spa+eng")
                doc.ocr_engine = "tesseract"
                doc.ocr_version = os.getenv("TESSERACT_VERSION", "")

                doc.estado = "procesado"
                doc.save()
                created += 1

        except IntegrityError:
            # Duplicado por hash (o por folio/rut/tipo). Lo damos por omitido.
            skipped += 1

        except Exception as e:
            # Marca error si el doc existe
            try:
                if 'doc' in locals() and doc.pk:
                    doc.estado = "error"
                    doc.save(update_fields=["estado"])
            except Exception:
                pass
            errors.append(f"{getattr(f, 'name', 'archivo')}: {str(e)}")

    return JsonResponse({"created": created, "skipped": skipped, "errors": errors})
