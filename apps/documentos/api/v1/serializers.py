# apps/documentos/api/v1/serializers.py
from rest_framework import serializers
from ...models import Documento


class DocumentoSerializer(serializers.ModelSerializer):
    """
    Serializer v1 para Documentos.
    Expone campos de negocio + estado SII para que el front los muestre.
    Los campos SII son de solo lectura; se actualizan vía acciones/Tasks.
    """

    class Meta:
        model = Documento
        fields = [
            "id",
            "empresa",
            "tipo_documento",
            "folio",
            "rut_proveedor",
            "razon_social_proveedor",
            "monto_neto",
            "monto_exento",
            "iva",
            "total",
            "estado",
            # —— SII ——
            "validado_sii",
            "sii_estado",
            "sii_track_id",
            "sii_glosa",
            "sii_validado_en",
            # —— fechas/archivos ——
            "fecha_emision",
            "archivo",
            "creado_en",
        ]
        read_only_fields = [
            # controlados por backend/procesos
            "empresa",
            "estado",
            # SII solo lectura desde la API pública (se actualiza por actions/tasks)
            "validado_sii",
            "sii_estado",
            "sii_track_id",
            "sii_glosa",
            "sii_validado_en",
            # timestamps/archivo cargado por flujo de upload
            "creado_en",
            "archivo",
        ]

    # (Opcional) si quieres normalizar salida de fechas/None → "" para el front:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Asegurar string ISO o "": la UI lo espera así en algunas vistas
        if data.get("fecha_emision") is None:
            data["fecha_emision"] = ""
        return data
