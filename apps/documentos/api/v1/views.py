# apps/documentos/api/v1/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import DocumentoSerializer
from .permissions import IsCompanyMember
from .filters import apply_document_filters
from .pagination import DefaultPagination

from ...selectors import documentos_de_empresas
from ...services.upload_service import create_documents_from_files
from ...services.storage_service import make_presigned_url
from apps.empresas.models import EmpresaUsuario
from apps.sii.services.sii_integration import validar_documento_con_sii, refrescar_estado_sii
# ajusta si tu módulo difiere
from apps.documentos.models import Documento
from apps.sii.tasks import start_sii_validation_core, refresh_sii_estado_documento

class DocumentoViewSet(viewsets.ModelViewSet):
    """
    /api/v1/documentos/                -> GET list (paginado + filtros), POST upload (multipart)
    /api/v1/documentos/{id}/           -> GET retrieve
    /api/v1/documentos/{id}/progress/  -> GET progreso individual
    /api/v1/documentos/progress-batch/ -> GET progreso masivo ?ids=1,2,3
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    serializer_class = DocumentoSerializer
    pagination_class = DefaultPagination
    queryset = Documento.objects.none()  # DRF sanity; usamos get_queryset abajo

    def get_queryset(self):
        empresa_ids = EmpresaUsuario.objects.filter(
            usuario=self.request.user
        ).values_list("empresa_id", flat=True)
        qs = documentos_de_empresas(empresa_ids)
        qs = apply_document_filters(self.request, qs)
        return qs.order_by("-creado_en")

    def create(self, request, *args, **kwargs):
        """
        Upload multipart: files[] o files. Encola OCR con Celery.
        Además: deja SII en EN_PROCESO y dispara validación automática por cada doc creado.
        """
        result = create_documents_from_files(request.user, request.FILES)

        # robustez: detectar ids creados en diferentes formatos de respuesta
        created_ids = []
        for key in ("created_ids", "ids", "created"):
            val = result.get(key)
            if isinstance(val, list):
                for x in val:
                    if isinstance(x, int):
                        created_ids.append(x)
                    elif isinstance(x, dict) and "id" in x:
                        created_ids.append(int(x["id"]))
        created_ids = list(dict.fromkeys(created_ids))  # únicos manteniendo orden

        if created_ids:
            # marcar EN_PROCESO y disparar validación SII con escalados realistas
            docs = Documento.objects.filter(id__in=created_ids)
            for doc in docs:
                if (doc.sii_estado or "") != "EN_PROCESO":
                    doc.sii_estado = "EN_PROCESO"
                    doc.validado_sii = False
                    doc.save(update_fields=["sii_estado", "validado_sii"])
                try:
                    # corre en background si tienes worker; en dev eager=True igual funciona
                    start_sii_validation_core.delay(doc.id)
                except Exception:
                    start_sii_validation_core.apply_async(args=[doc.id])

        status_code = status.HTTP_201_CREATED if result.get("created") else status.HTTP_200_OK
        return Response(result, status=status_code)

    @action(detail=True, methods=["get"], url_path="progress")
    def progress(self, request, pk=None):
        doc = self.get_queryset().filter(pk=pk).first()
        if not doc:
            return Response({"detail": "Documento no encontrado"}, status=404)
        data = {
            "id": doc.id,
            "estado": doc.estado,
            "tipo_documento": doc.tipo_documento,
            "folio": doc.folio or "",
            "rut_proveedor": doc.rut_proveedor or "",
            "razon_social_proveedor": doc.razon_social_proveedor or "",
            "monto_neto": float(doc.monto_neto) if doc.monto_neto is not None else None,
            "monto_exento": float(doc.monto_exento) if doc.monto_exento is not None else None,
            "iva": float(doc.iva) if doc.iva is not None else None,
            "total": float(doc.total) if doc.total is not None else None,
            "fecha_emision": doc.fecha_emision.isoformat() if doc.fecha_emision else "",
            "validado_sii": doc.validado_sii,
            "sii_estado": doc.sii_estado,
        }
        return Response({"ok": True, "documento": data})

    @action(detail=False, methods=["get"], url_path="progress-batch")
    def progress_batch(self, request):
        ids = request.query_params.get("ids", "")
        try:
            id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]
        except Exception:
            id_list = []
        docs = self.get_queryset().filter(id__in=id_list)
        payload = []
        for d in docs:
            payload.append({
                "id": d.id,
                "estado": d.estado,
                "tipo_documento": d.tipo_documento,
                "folio": d.folio or "",
                "rut_proveedor": d.rut_proveedor or "",
                "razon_social_proveedor": d.razon_social_proveedor or "",
                "monto_neto": float(d.monto_neto) if d.monto_neto is not None else None,
                "monto_exento": float(d.monto_exento) if d.monto_exento is not None else None,
                "iva": float(d.iva) if d.iva is not None else None,
                "total": float(d.total) if d.total is not None else None,
                "fecha_emision": d.fecha_emision.isoformat() if d.fecha_emision else "",
                "validado_sii": d.validado_sii,
                "sii_estado": d.sii_estado,
            })
        return Response({"ok": True, "documentos": payload})

    @action(detail=True, methods=["post"], url_path="validar-sii", permission_classes=[IsAuthenticated, IsCompanyMember])
    def validar_sii(self, request, pk=None):
        """
        Dispara la validación SII (Mock/Real) para este documento.
        Requiere: rut_proveedor, total, fecha_emision, folio, tipo_documento.
        """
        doc = self.get_queryset().filter(pk=pk).first()
        if not doc:
            return Response({"detail": "Documento no encontrado"}, status=404)

        missing = []
        if not doc.rut_proveedor: missing.append("rut_proveedor")
        if not doc.total: missing.append("total")
        if not doc.fecha_emision: missing.append("fecha_emision")
        if not doc.folio: missing.append("folio")
        if not doc.tipo_documento: missing.append("tipo_documento")
        if missing:
            return Response({"ok": False, "detail": "Faltan campos para validar", "missing": missing}, status=400)

        res = validar_documento_con_sii(request, doc)

        # primer refresh en background para “casi tiempo real”
        try:
            refresh_sii_estado_documento.delay(doc.id)
        except Exception:
            pass

        return Response({"ok": True, "result": res, "documento_id": doc.id}, status=200 if res.get("ok") else 202)

    @action(detail=True, methods=["get"], url_path="estado-sii", permission_classes=[IsAuthenticated, IsCompanyMember])
    def estado_sii(self, request, pk=None):
        """
        Consulta el estado en SII para este documento por track_id y actualiza sii_estado/glosa.
        """
        doc = self.get_queryset().filter(pk=pk).first()
        if not doc:
            return Response({"detail": "Documento no encontrado"}, status=404)
        res = refrescar_estado_sii(request, doc)
        # si no hay track_id o error de negocio, devolvemos 200 con ok:false para no ensuciar consola del front
        ok = bool(res.get("ok", True))
        return Response({"ok": ok, "result": res, "documento_id": doc.id}, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def presign_upload(request):
    filename = request.data.get("filename")
    content_type = request.data.get("content_type", "application/octet-stream")
    if not filename:
        return Response({"detail": "filename requerido"}, status=400)
    data = make_presigned_url(request.user, filename, content_type)
    return Response(data, status=200)
