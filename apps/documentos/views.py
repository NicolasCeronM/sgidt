from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_date
from .models import Documento

@login_required
def documentos_page(request):
    return render(request, "panel/documentos.html")  # tu frontend

@login_required
@require_GET
def documentos_list_api(request):
    user = request.user
    qs = Documento.objects.select_related("empresa").all() if user.is_superuser \
         else Documento.objects.filter(empresa=user.empresas_propias.first())

    # filtros
    date_from = request.GET.get("dateFrom")
    date_to   = request.GET.get("dateTo")
    doc_type  = request.GET.get("docType")
    doc_status= request.GET.get("docStatus")

    if date_from:
        df = parse_date(date_from)
        if df: qs = qs.filter(creado_en__date__gte=df)
    if date_to:
        dt = parse_date(date_to)
        if dt: qs = qs.filter(creado_en__date__lte=dt)

    if doc_type:
        mapper = {
            "factura": ["factura_afecta","factura_exenta"],
            "boleta": ["boleta"],
            "nota-credito": ["nota_credito"],
        }
        t = mapper.get(doc_type, [])
        if t: qs = qs.filter(tipo__in=t)

    if doc_status:
        st_map = {"validado":"Vigente", "pendiente":"Pendiente", "error":"Error"}
        estado = st_map.get(doc_status)
        if estado: qs = qs.filter(estado_sii__iexact=estado)

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
    user = request.user
    empresa = user.empresas_propias.first() if not user.is_superuser else None
    if not user.is_superuser and not empresa:
        return HttpResponseBadRequest("Usuario sin empresa asociada.")

    files = request.FILES.getlist("files[]") or request.FILES.getlist("files")
    if not files:
        return HttpResponseBadRequest("No se enviaron archivos.")

    allowed_ext = {".pdf", ".jpg", ".jpeg", ".png"}
    max_size = 10 * 1024 * 1024
    created, skipped, errors = 0, 0, []

    for f in files:
        name = f.name.lower()
        if not any(name.endswith(ext) for ext in allowed_ext):
            errors.append(f"{f.name}: formato no permitido")
            continue
        if f.size > max_size:
            errors.append(f"{f.name}: excede 10MB")
            continue
        try:
            doc = Documento(
                empresa = empresa if empresa else user.empresas_propias.first(),
                subido_por = user,
                archivo = f
            )
            doc.save()   # UniqueConstraint controla duplicados por hash
            created += 1
        except Exception as e:
            if "uniq_doc_hash_empresa" in str(e):
                skipped += 1
            else:
                errors.append(f"{f.name}: {str(e)}")

    return JsonResponse({"created": created, "skipped": skipped, "errors": errors})
