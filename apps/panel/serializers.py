# panel/serializers.py
from rest_framework import serializers
from apps.documentos.models import Documento  # ajusta el import si tu modelo vive en otra app

class DocumentoMiniSerializer(serializers.ModelSerializer):
    tipo_display = serializers.SerializerMethodField()
    fecha_emision = serializers.DateField(format="%d/%m/%Y", required=False, allow_null=True)
    creado_en = serializers.DateTimeField(format="%d/%m/%Y %H:%M", required=False)

    class Meta:
        model = Documento
        fields = (
            "id",
            "tipo_documento",
            "tipo_display",
            "folio",
            "razon_social_proveedor",
            "estado",
            "fecha_emision",
            "creado_en",
            "total",
            "iva",
        )

    def get_tipo_display(self, obj):
        return obj.get_tipo_documento_display()
