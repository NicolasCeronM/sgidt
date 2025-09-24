# apps/sii/views.py
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ConsultaContribuyenteQuery,
    ValidarDTEBody,
    EstadoDTEQuery,
    RecibirDTEBody,
)
from .services.client import get_provider
from .models import SIITransaccion, SIIContribuyenteCache
from .utils import resolve_empresa_for_request

# Intentamos usar tu permiso de empresa si existe; si no, caemos a IsAuthenticated
try:
    # Ajusta el import si tu permiso vive en otro módulo
    from apps.documentos.api.v1.permissions import IsCompanyMember
    BasePerm = type("BasePerm", (permissions.IsAuthenticated, IsCompanyMember), {})
except Exception:
    BasePerm = permissions.IsAuthenticated


class ConsultaContribuyenteView(APIView):
    permission_classes = [BasePerm]

    def get(self, request):
        q = ConsultaContribuyenteQuery(data=request.query_params)
        q.is_valid(raise_exception=True)

        empresa = resolve_empresa_for_request(request)
        rut_req = q.validated_data["rut"]

        # TTL 30 minutos para cache
        cache = SIIContribuyenteCache.objects.filter(rut=rut_req).first()
        if cache and cache.is_fresh(minutes=30):
            payload = {
                "rut": cache.rut,
                "razon_social": cache.razon_social,
                "actividad_principal": cache.actividad_principal,
                "estado": cache.estado,
            }
            # Traza (cache-hit)
            SIITransaccion.objects.create(
                empresa=empresa,
                endpoint="contribuyente",
                track_id=None,
                request_payload={"rut": rut_req, "cache": True},
                response_payload=payload,
                ok=True,
                status_code=200,
                estado="CACHE",
            )
            return Response(payload, status=status.HTTP_200_OK)

        # Si no hay cache fresco -> consultar provider y refrescar cache
        prov = get_provider()
        c = prov.consulta_contribuyente(rut_req)

        SIIContribuyenteCache.objects.update_or_create(
            rut=rut_req,
            defaults={
                "razon_social": c.razon_social,
                "actividad_principal": c.actividad_principal,
                "estado": c.estado,
                "refreshed_at": timezone.now(),
            },
        )

        resp = {
            "rut": c.rut,
            "razon_social": c.razon_social,
            "actividad_principal": c.actividad_principal,
            "estado": c.estado,
        }

        SIITransaccion.objects.create(
            empresa=empresa,
            endpoint="contribuyente",
            track_id=None,
            request_payload={"rut": rut_req},
            response_payload=resp,
            ok=True,
            status_code=200,
        )
        return Response(resp, status=status.HTTP_200_OK)


class ValidarDTEView(APIView):
    permission_classes = [BasePerm]

    def post(self, request):
        s = ValidarDTEBody(data=request.data)
        s.is_valid(raise_exception=True)

        empresa = resolve_empresa_for_request(request)
        prov = get_provider()
        res = prov.validar_dte(**s.validated_data)

        # Traza
        SIITransaccion.objects.create(
            empresa=empresa,
            endpoint="validar_dte",
            track_id=res.get("track_id"),
            request_payload=s.validated_data,
            response_payload=res,
            ok=bool(res.get("ok", False)),
            status_code=200 if res.get("ok") else 202,
            estado=("ACEPTADO" if res.get("ok") else "RECHAZADO"),
        )

        return Response(
            res,
            status=status.HTTP_200_OK if res.get("ok") else status.HTTP_202_ACCEPTED,
        )


class EstadoDTEView(APIView):
    permission_classes = [BasePerm]

    def get(self, request):
        q = EstadoDTEQuery(data=request.query_params)
        q.is_valid(raise_exception=True)

        empresa = resolve_empresa_for_request(request)
        prov = get_provider()
        res = prov.estado_dte(q.validated_data["track_id"])

        # Traza
        SIITransaccion.objects.create(
            empresa=empresa,
            endpoint="estado_dte",
            track_id=q.validated_data["track_id"],
            request_payload=q.validated_data,
            response_payload=res,
            ok=res.get("estado") == "ACEPTADO",
            status_code=200,
            estado=res.get("estado"),
        )

        return Response(res, status=status.HTTP_200_OK)


class RecibirDTEView(APIView):
    permission_classes = [BasePerm]

    def post(self, request):
        s = RecibirDTEBody(data=request.data)
        s.is_valid(raise_exception=True)

        empresa = resolve_empresa_for_request(request)
        prov = get_provider()
        res = prov.recibir_dte(**s.validated_data)

        # Traza
        SIITransaccion.objects.create(
            empresa=empresa,
            endpoint="recibir_dte",
            track_id=res.get("track_id"),
            request_payload={
                "filename": s.validated_data["filename"],
                "xml_len": len(s.validated_data["xml_base64"]),
            },
            response_payload=res,
            ok=True,
            status_code=201,
            estado="RECIBIDO",
        )

        return Response(res, status=status.HTTP_201_CREATED)
