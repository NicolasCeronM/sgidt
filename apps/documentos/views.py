from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_date
from django.db import IntegrityError

from .models import Documento


@login_required
def documentos_page(request):
    """Renderiza el panel de documentos (frontend)."""
    return render(request, "panel/documentos.html")


@login_required
@require_GET
def documentos_list_api(request):
    """
    API de listado con filtros:
      - dateFrom, dateTo: YYYY-MM-DD
      - docType: factura | boleta | nota-credito
      - docStatus: validado | pendiente | error
    """
    user = request.user

    if user.is_superuser:
        qs = Documento.objects.select_related("empresa").all()
    else:
        empresa = user.empresas_propias.first()
        if not empresa:
            return JsonResponse({"results": []})
        qs = Documento.objects.select_related("empresa").filter(empresa=empresa)

    date_from = request.GET.get("dateFrom")
    date_to = request.GET.get("dateTo")
    doc_type = request.GET.get("docType")
    doc_status = request.GET.get("docStatus")

    if date_from:
        df = parse_date(date_from)
        if df:
            qs = qs.filter(creado_en__date__gte=df)
    if date_to:
        dt = parse_date(date_to)
        if dt:
            qs = qs.filter(creado_en__date__lte=dt)

    if doc_type:
        mapper = {
            "factura": ["factura_afecta", "factura_exenta"],
            "boleta": ["boleta"],
            "nota-credito": ["nota_credito"],
        }
        types = mapper.get(doc_type, [])
        if types:
            qs = qs.filter(tipo__in=types)

    if doc_status:
        st_map = {"validado": "Vigente", "pendiente": "Pendiente", "error": "Error"}
        estado = st_map.get(doc_status)
        if estado:
            qs = qs.filter(estado_sii__iexact=estado)

    data = [{
        "id": d.id,
        "fecha": d.creado_en.strftime("%d/%m/%Y"),
        "tipo": d.get_tipo_display() if d.tipo else "—",
        "folio": d.folio or "—",
        "rut_emisor": d.rut_proveedor or "—",
        "monto": float(d.total) if d.total is not None else None,
        "estado": d.estado_sii or "—",
        "archivo_url": d.archivo.url if d.archivo else "",
    } for d in qs.order_by("-creado_en")[:500]]

    return JsonResponse({"results": data})


@login_required
@require_POST
def documentos_upload_api(request):
    """
    API de subida de archivos.
    - Valida extensión y tamaño.
    - Evita duplicados por hash (UniqueConstraint) y los cuenta como 'skipped'.
    Devuelve: {created, skipped, errors: []}
    """
    user = request.user

    if user.is_superuser:
        empresa = user.empresas_propias.first()
        if not empresa:
            return HttpResponseBadRequest("El superusuario no tiene empresa asociada.")
    else:
        empresa = user.empresas_propias.first()
        if not empresa:
            return HttpResponseBadRequest("Usuario sin empresa asociada.")

    files = request.FILES.getlist("files[]") or request.FILES.getlist("files")
    if not files:
        return HttpResponseBadRequest("No se enviaron archivos.")

    allowed_ext = {".pdf", ".jpg", ".jpeg", ".png"}
    max_size = 10 * 1024 * 1024  # 10MB

    created, skipped, errors = 0, 0, []

    for f in files:
        name_l = (f.name or "").lower()
        if not any(name_l.endswith(ext) for ext in allowed_ext):
            errors.append(f"{f.name}: formato no permitido")
            continue
        if f.size and f.size > max_size:
            errors.append(f"{f.name}: excede 10MB")
            continue

        try:
            doc = Documento(
                empresa=empresa,
                subido_por=user,
                archivo=f,
            )
            doc.save()
            created += 1

        except IntegrityError:
            skipped += 1

        except Exception as e:
            msg = str(e)
            if "UNIQUE constraint" in msg and "hash_sha256" in msg:
                skipped += 1
            else:
                errors.append(f"{f.name}: {msg}")

    return JsonResponse({"created": created, "skipped": skipped, "errors": errors})
