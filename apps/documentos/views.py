from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_date
from django.db import IntegrityError
from datetime import date, datetime
from decimal import Decimal

from .models import Documento
from apps.empresas.models import Empresa, EmpresaUsuario
from apps.documentos import ocr
import os

def _empresa_ids_del_usuario(user):
    """Retorna IDs de empresas a las que pertenece el usuario vía EmpresaUsuario."""
    return EmpresaUsuario.objects.filter(usuario=user).values_list("empresa_id", flat=True)

# -------------------------------------------------------------------
# Helper: convierte cualquier estructura (dict/list) a una versión
# JSON‑serializable. En particular, transforma Decimal -> float.
# -------------------------------------------------------------------
def _to_jsonable(obj):
    # Tipos escalares especiales
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    
    # Contenedores
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_to_jsonable(x) for x in obj)
    if isinstance(obj, set):
        return [_to_jsonable(x) for x in obj]  # set -> lista JSON

    # Otros tipos quedan tal cual (str, int, float, None, bool)
    return obj


# -------------------------------------------------------------------
# Página HTML del módulo de documentos (panel)
# Requiere autenticación.
# -------------------------------------------------------------------
@login_required
def documentos_page(request):
    """Renderiza el panel de documentos (frontend)."""
    return render(request, "panel/documentos.html")


# -------------------------------------------------------------------
# API: listar documentos del usuario autenticado.
# - Filtros opcionales por fecha_desde, fecha_hasta, tipo, estado.
# - Limita a las empresas cuyo propietario es el usuario logueado.
# - Devuelve un JSON con los campos necesarios para la tabla.
# -------------------------------------------------------------------
@login_required
@require_GET
def documentos_list_api(request):
    # 1) Restringe por empresas donde el usuario es miembro
    empresa_ids = list(_empresa_ids_del_usuario(request.user))
    qs = Documento.objects.filter(empresa_id__in=empresa_ids).order_by("-creado_en")

    # 2) Lee filtros desde querystring (se aceptan dos alias por campo)
    f_desde = request.GET.get("from") or request.GET.get("date_from")
    f_hasta = request.GET.get("to") or request.GET.get("date_to")
    tipo = request.GET.get("type") or request.GET.get("docType")
    estado = request.GET.get("status") or request.GET.get("docStatus")

    # 3) Normaliza y aplica filtro fecha_desde
    fecha_desde = parse_date(f_desde) if f_desde else None
    if isinstance(fecha_desde, datetime):
        fecha_desde = fecha_desde.date()
    if isinstance(fecha_desde, date):
        qs = qs.filter(fecha_emision__gte=fecha_desde)

    # 4) Normaliza y aplica filtro fecha_hasta
    fecha_hasta = parse_date(f_hasta) if f_hasta else None
    if isinstance(fecha_hasta, datetime):
        fecha_hasta = fecha_hasta.date()
    if isinstance(fecha_hasta, date):
        qs = qs.filter(fecha_emision__lte=fecha_hasta)

    # 5) Filtros por tipo/estado si vienen
    if tipo:
        qs = qs.filter(tipo_documento=tipo)
    if estado:
        qs = qs.filter(estado=estado)

    # 6) Serializa resultados (capado a 200 por seguridad/UX)
    data = []
    for d in qs[:200]:
        data.append({
            "id": d.id,
            "fecha": d.fecha_emision.isoformat() if d.fecha_emision else "",
            "tipo": d.tipo_documento,
            "folio": d.folio,
            "rut_emisor": d.rut_proveedor,
            # JsonResponse serializa float; Decimal se castea aquí por seguridad.
            "total": float(d.total) if d.total is not None else None,
            "estado": d.estado,
            "archivo": d.archivo.url if d.archivo else "",
        })
    return JsonResponse({"results": data})


# -------------------------------------------------------------------
# API: subir y procesar documentos (PDF/JPG/PNG).
# Flujo:
#  - Selecciona la primera empresa del usuario (MVP).
#  - Guarda el archivo -> calcula hash -> evita duplicados (UniqueConstraint).
#  - Parsea/OCR en forma sincrónica (MVP) y persiste campos extraídos.
#  - Devuelve conteo de creados/omitidos y lista de errores (si hay).
# -------------------------------------------------------------------
@login_required
@require_POST
def documentos_upload_api(request):
    # --- Empresa activa desde sesión si existe ---
    empresa = None
    eid = request.session.get("empresa_activa_id")
    if eid:
        # Valida que el usuario tenga membresía en esa empresa
        if EmpresaUsuario.objects.filter(usuario=request.user, empresa_id=eid).exists():
            empresa = Empresa.objects.filter(id=eid).first()

    # --- Si no hay activa válida, toma la primera empresa donde es miembro (MVP) ---
    if not empresa:
        eu = EmpresaUsuario.objects.filter(usuario=request.user).select_related("empresa").first()
        if eu:
            empresa = eu.empresa

    if not empresa:
        return HttpResponseBadRequest("Debes crear primero una empresa o no tienes permisos en ninguna.")

    # 2) Obtiene archivos desde el form-data (admite 'files[]' o 'files')
    files = request.FILES.getlist("files[]") or request.FILES.getlist("files")
    if not files:
        return HttpResponseBadRequest("No se recibieron archivos")

    created = 0
    skipped = 0
    errors = []

    for f in files:
        try:
            doc = Documento(
                empresa=empresa,
                subido_por=request.user,
                archivo=f,
                estado="procesando",
            )
            doc.save()

            # Parsing/OCR (igual que antes)
            local_path = doc.archivo.path
            result = ocr.parse_file(local_path, doc.mime_type)
            doc.ocr_json = _to_jsonable(result)

            # Persistencia de campos extraídos (igual)
            doc.tipo_documento = result.get("tipo_documento", "desconocido")
            doc.folio = result.get("folio") or ""
            doc.fecha_emision = result.get("fecha_emision")
            doc.rut_proveedor = result.get("rut_proveedor") or ""
            doc.monto_neto = result.get("monto_neto")
            doc.monto_exento = result.get("monto_exento")
            doc.iva = result.get("iva")
            doc.total = result.get("total")

            doc.estado = "procesado"
            doc.save()
            created += 1

        except IntegrityError:
            skipped += 1

        except Exception as e:
            if 'doc' in locals():
                doc.estado = "error"
                doc.save(update_fields=["estado"])
            errors.append(f"{getattr(f, 'name', 'archivo')}: {str(e)}")

    return JsonResponse({"created": created, "skipped": skipped, "errors": errors})
