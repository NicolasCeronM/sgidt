from rest_framework import serializers

# Serializer para los KPIs principales (las tarjetas)
class ReporteKpiSerializer(serializers.Serializer):
    total_ingresos = serializers.IntegerField()
    total_gastos = serializers.IntegerField()
    resultado_mes = serializers.IntegerField()

# Serializer para el gráfico de Ingresos vs. Gastos
class IngresosVsGastosChartSerializer(serializers.Serializer):
    ingresos = serializers.IntegerField()
    gastos = serializers.IntegerField()

# Serializer para el gráfico de Análisis de IVA
class AnalisisIvaChartSerializer(serializers.Serializer):
    iva_credito = serializers.IntegerField()
    iva_debito = serializers.IntegerField()

# Serializer principal que anidará a los demás
class ReporteGeneralSerializer(serializers.Serializer):
    kpis = ReporteKpiSerializer()
    ingresos_vs_gastos_chart = IngresosVsGastosChartSerializer()
    analisis_iva_chart = AnalisisIvaChartSerializer()
    distribucion_ingresos_chart = serializers.DictField(child=serializers.IntegerField())
    distribucion_gastos_chart = serializers.DictField(child=serializers.IntegerField())