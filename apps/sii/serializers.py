# apps/sii/serializers.py
from rest_framework import serializers
import re
from datetime import date

RUT_RE = re.compile(r"^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$|^\d{7,8}-[\dkK]$")

class ConsultaContribuyenteQuery(serializers.Serializer):
    rut = serializers.CharField()

    def validate_rut(self, v):
        v = v.strip()
        if not RUT_RE.match(v):
            raise serializers.ValidationError("RUT inválido (formato esperado 11111111-1).")
        return v

class ValidarDTEBody(serializers.Serializer):
    emisor_rut   = serializers.CharField()
    receptor_rut = serializers.CharField()
    tipo_dte     = serializers.IntegerField()  # 33, 34, 52, etc.
    folio        = serializers.IntegerField(min_value=1)
    monto_total  = serializers.IntegerField(min_value=0)
    fecha_emision = serializers.DateField()
    ted = serializers.CharField(allow_blank=True)  # En mock no exigimos estructura real

    def validate(self, data):
        for k in ("emisor_rut","receptor_rut"):
            if not RUT_RE.match(data[k]):
                raise serializers.ValidationError({k:"RUT inválido"})
        if data["fecha_emision"] > date.today():
            raise serializers.ValidationError({"fecha_emision":"No puede ser futura."})
        return data

class EstadoDTEQuery(serializers.Serializer):
    track_id = serializers.CharField()

class RecibirDTEBody(serializers.Serializer):
    xml_base64 = serializers.CharField()
    filename   = serializers.CharField()
