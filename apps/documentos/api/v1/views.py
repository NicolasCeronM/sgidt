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

    def get_queryset(self):
        empresa_ids = EmpresaUsuario.objects.filter(
            usuario=self.request.user
        ).values_list("empresa_id", flat=True)
        qs = documentos_de_empresas(empresa_ids)
        qs = apply_document_filters(self.request, qs)
        return qs.order_by("-creado_en")

    def create(self, request, *args, **kwargs):
        """Upload multipart: files[] o files. Encola OCR con Celery."""
        result = create_documents_from_files(request.user, request.FILES)
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

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def presign_upload(request):
    filename = request.data.get("filename")
    content_type = request.data.get("content_type", "application/octet-stream")
    if not filename:
        return Response({"detail": "filename requerido"}, status=400)
    data = make_presigned_url(request.user, filename, content_type)
    return Response(data, status=200)
