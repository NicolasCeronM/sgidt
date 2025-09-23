from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .permissions import IsAuthenticatedCompany
from .serializers import (
    ConsultaContribuyenteQuery, ValidarDTEBody, EstadoDTEQuery, RecibirDTEBody
)
from .services.client import get_provider

# Create your views here.

class ConsultaContribuyenteView(APIView):
    permission_classes = [IsAuthenticatedCompany]

    def get(self, request):
        q = ConsultaContribuyenteQuery(data=request.query_params)
        q.is_valid(raise_exception=True)
        prov = get_provider()
        c = prov.consulta_contribuyente(q.validated_data["rut"])
        return Response({
            "rut": c.rut,
            "razon_social": c.razon_social,
            "actividad_principal": c.actividad_principal,
            "estado": c.estado
        })

class ValidarDTEView(APIView):
    permission_classes = [IsAuthenticatedCompany]

    def post(self, request):
        s = ValidarDTEBody(data=request.data)
        s.is_valid(raise_exception=True)
        prov = get_provider()
        res = prov.validar_dte(**s.validated_data)
        return Response(res, status=status.HTTP_200_OK if res["ok"] else status.HTTP_202_ACCEPTED)

class EstadoDTEView(APIView):
    permission_classes = [IsAuthenticatedCompany]

    def get(self, request):
        q = EstadoDTEQuery(data=request.query_params)
        q.is_valid(raise_exception=True)
        prov = get_provider()
        res = prov.estado_dte(q.validated_data["track_id"])
        return Response(res)

class RecibirDTEView(APIView):
    permission_classes = [IsAuthenticatedCompany]

    def post(self, request):
        s = RecibirDTEBody(data=request.data)
        s.is_valid(raise_exception=True)
        prov = get_provider()
        res = prov.recibir_dte(**s.validated_data)
        return Response(res, status=status.HTTP_201_CREATED)
