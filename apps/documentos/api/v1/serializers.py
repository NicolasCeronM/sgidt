# apps/documentos/api/v1/serializers.py
from rest_framework import serializers
from ...models import Documento

class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = [
            "id","empresa","tipo_documento","folio","rut_proveedor","razon_social_proveedor",
            "monto_neto","monto_exento","iva","total","estado","validado_sii","sii_estado",
            "fecha_emision","archivo","creado_en",
        ]
        read_only_fields = ["empresa","estado","validado_sii","sii_estado","creado_en","archivo"]
