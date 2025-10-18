import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:fl_chart/fl_chart.dart'; // <-- 1. IMPORTAR FL_CHART

// import 'main_screen.dart';

class ReportesScreen extends StatefulWidget {
  const ReportesScreen({super.key});

  @override
  State<ReportesScreen> createState() => _ReportesScreenState();
}

class _ReportesScreenState extends State<ReportesScreen> {
  // --- INTERRUPTOR ---
  final bool _useMockData = true; 
  // ---
  
  bool _isLoading = true;
  String? _error;

  String _totalGastado = "-\$";
  String _documentosProcesados = "-";
  late DateTimeRange _periodoSeleccionado;
  String _textoPeriodo = "Cargando...";

  // <-- 2. DATOS SIMULADOS PARA LOS GRÁFICOS -->
  // (En el futuro, estos se cargarán desde la API en _loadData)
  List<BarChartGroupData> _barChartData = [];
  List<PieChartSectionData> _pieChartData = [];


  @override
  void initState() {
    super.initState();
    initializeDateFormatting('es'); 
    
    final now = DateTime.now();
    final primerDiaMes = DateTime(now.year, now.month, 1);
    final ultimoDiaMes = DateTime(now.year, now.month + 1, 0);
    _periodoSeleccionado = DateTimeRange(start: primerDiaMes, end: ultimoDiaMes);
    _textoPeriodo = _formatRange(_periodoSeleccionado, now);

    _loadData();
  }

  String _formatRange(DateTimeRange range, DateTime now) {
    final DateFormat formatterDiaMes = DateFormat('d MMM', 'es');
    final DateFormat formatterMesAnyo = DateFormat('MMMM yyyy', 'es');

    if (range.start.year == now.year && range.start.month == now.month && range.start.day == 1 &&
        range.end.month == now.month && range.end.day == DateTime(now.year, now.month + 1, 0).day) {
      return "Este Mes";
    }
    
    return "${formatterDiaMes.format(range.start)} - ${formatterDiaMes.format(range.end)}, ${range.end.year}";
  }


  Future<void> _loadData() async {
    if (!_isLoading) {
      setState(() => _isLoading = true);
    }
    setState(() => _error = null);

    try {
      if (_useMockData) {
        await _loadMockData(_periodoSeleccionado);
      } else {
        await _loadRealData(_periodoSeleccionado);
      }
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  /// Carga datos simulados (Frontend)
  Future<void> _loadMockData(DateTimeRange periodo) async {
    await Future.delayed(const Duration(milliseconds: 1500));
    if (!mounted) return;
    
    setState(() {
      // Datos KPI
      _totalGastado = "\$639.617";
      _documentosProcesados = "4";

      // <-- 3. GENERAR DATOS SIMULADOS PARA GRÁFICOS -->
      _barChartData = _getMockBarData();
      _pieChartData = _getMockPieData();
    });
  }

  /// Carga datos reales desde el endpoint
  Future<void> _loadRealData(DateTimeRange periodo) async {
    try {
      final String fechaInicio = periodo.start.toIso8601String().split('T').first;
      final String fechaFin = periodo.end.toIso8601String().split('T').first;

      final url = Uri.parse('https://api.tu-dominio.com/reportes').replace(
        queryParameters: {
          'fecha_inicio': fechaInicio,
          'fecha_fin': fechaFin,
        },
      );
      
      final response = await http.get(url).timeout(const Duration(seconds: 10));
      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          // Datos KPI
          double total = (data['totalGastado'] ?? 0.0).toDouble();
          int docs = (data['documentosProcesados'] ?? 0).toInt();
          _totalGastado = "\$${total.toStringAsFixed(0)}";
          _documentosProcesados = docs.toString();

          // <-- 4. GENERAR DATOS REALES PARA GRÁFICOS (A FUTURO) -->
          // (Aquí llamarías a funciones que parsen el JSON de la API)
          // _barChartData = _parseBarDataFromApi(data['gastosCategoria']);
          // _pieChartData = _parsePieDataFromApi(data['tiposDocumento']);

          // Por ahora, usamos los simulados también en el modo real
          _barChartData = _getMockBarData();
          _pieChartData = _getMockPieData();
        });
      } else {
        throw Exception("Error del servidor: ${response.statusCode}");
      }
    } catch (e) {
      throw Exception("Error de conexión: $e");
    }
  }

  // --- Funciones de selección de período (sin cambios) ---
  Future<void> _seleccionarPeriodo() async {
    final DateTimeRange? newRange = await showDateRangePicker(
      context: context,
      initialDateRange: _periodoSeleccionado,
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      locale: const Locale('es'),
    );

    if (newRange != null && newRange != _periodoSeleccionado) {
      setState(() {
        _periodoSeleccionado = newRange;
        _textoPeriodo = _formatRange(newRange, DateTime.now());
      });
      _loadData();
    }
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SGIDT - Reportes'),
        centerTitle: true,
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? _buildErrorBody(_error!)
                : _buildReportBody(),
      ),
    );
  }

  /// Construye el cuerpo principal de la pantalla de reportes
  Widget _buildReportBody() {
    final textTheme = Theme.of(context).textTheme;
    final colorScheme = Theme.of(context).colorScheme;

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16.0),
      children: [
        // --- Selector de Período ---
        Card(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: colorScheme.outlineVariant, width: 0.5),
          ),
          child: ListTile(
            title: const Text('Mostrando reporte de:'),
            trailing: TextButton(
              onPressed: _seleccionarPeriodo,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(_textoPeriodo, style: const TextStyle(fontSize: 16)),
                  const SizedBox(width: 4),
                  const Icon(Icons.calendar_month_outlined),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 20),

        // --- Tarjetas de Resumen (KPIs) ---
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 12,
          crossAxisSpacing: 12,
          childAspectRatio: 1.1,
          children: [
            _SummaryCard(
              title: "Total Gastado",
              value: _totalGastado,
              icon: Icons.receipt_long_outlined,
              color: colorScheme.primary,
            ),
            _SummaryCard(
              title: "Documentos",
              value: _documentosProcesados,
              icon: Icons.folder_copy_outlined,
              color: colorScheme.secondary,
            ),
          ],
        ),
        const SizedBox(height: 32),

        // <-- 5. SECCIÓN DE GRÁFICOS (REEMPLAZA EL PLACEHOLDER) -->
        Text(
          "Análisis Detallado",
          style: textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 24),
        
        // Gráfico de Barras
        _buildBarChart(context),

        const SizedBox(height: 32),

        // Gráfico Circular
        _buildPieChart(context),

      ],
    );
  }

  // --- (Widget _buildErrorBody sin cambios) ---
  Widget _buildErrorBody(String error) {
    return Center(
      // ... (código idéntico al anterior)
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.cloud_off_outlined,
                size: 60, color: Theme.of(context).colorScheme.error),
            const SizedBox(height: 16),
            Text(
              'Ocurrió un error',
              style: Theme.of(context).textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              onPressed: _loadData,
            ),
          ],
        ),
      ),
    );
  }


  // --- <-- 6. NUEVOS WIDGETS PARA LOS GRÁFICOS --> ---

  /// Construye el gráfico de barras
  Widget _buildBarChart(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final colorScheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Gastos por Categoría", style: textTheme.titleMedium),
        const SizedBox(height: 16),
        SizedBox(
          height: 200,
          child: BarChart(
            BarChartData(
              alignment: BarChartAlignment.spaceAround,
              barTouchData: BarTouchData(enabled: false), // Deshabilita tooltips por ahora
              borderData: FlBorderData(show: false), // Sin bordes
              gridData: FlGridData(show: false), // Sin grilla
              
              // Títulos del eje Y (izquierda)
              titlesData: FlTitlesData(
                show: true,
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                // Títulos del eje X (abajo)
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (double value, TitleMeta meta) {
                      String text = '';
                      switch (value.toInt()) {
                        case 0: text = 'Combus.'; break;
                        case 1: text = 'Peajes'; break;
                        case 2: text = 'Mant.'; break;
                        case 3: text = 'Otros'; break;
                      }
                      return Padding(
                        padding: const EdgeInsets.only(top: 8.0),
                        child: Text(text, style: textTheme.bodySmall),
                      );
                    },
                    reservedSize: 30,
                  ),
                ),
                // Títulos del eje Y (izquierda)
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 40,
                    getTitlesWidget: (value, meta) {
                      if (value == 0) return const Text('');
                      if (value % 100000 == 0) { // Muestra etiquetas cada 100k
                        return Text('${(value / 1000).round()}k', style: textTheme.bodySmall);
                      }
                      return const Text('');
                    },
                  ),
                ),
              ),

              // Datos de las barras
              barGroups: _barChartData,
            ),
          ),
        ),
      ],
    );
  }

  /// Construye el gráfico circular
  Widget _buildPieChart(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final colorScheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Tipos de Documento", style: textTheme.titleMedium),
        const SizedBox(height: 16),
        SizedBox(
          height: 200,
          child: PieChart(
            PieChartData(
              sections: _pieChartData,
              centerSpaceRadius: 60, // Radio del agujero central
              sectionsSpace: 2, // Espacio entre secciones
              pieTouchData: PieTouchData(enabled: false), // Sin interacción
            ),
          ),
        ),
        // (Opcional) Leyenda
        // ... aquí podrías generar una leyenda basada en los datos ...
      ],
    );
  }


  // --- <-- 7. FUNCIONES PARA DATOS SIMULADOS --> ---

  /// Genera datos simulados para el gráfico de barras
  List<BarChartGroupData> _getMockBarData() {
    final colorScheme = Theme.of(context).colorScheme;
    return [
      _makeBarGroup(0, 310000, colorScheme.primary),
      _makeBarGroup(1, 150000, colorScheme.secondary),
      _makeBarGroup(2, 100000, colorScheme.tertiary),
      _makeBarGroup(3, 79617, colorScheme.errorContainer),
    ];
  }

  /// Helper para crear una barra
  BarChartGroupData _makeBarGroup(int x, double y, Color color) {
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: y,
          color: color,
          width: 16,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(4),
            topRight: Radius.circular(4),
          ),
        ),
      ],
    );
  }

  /// Genera datos simulados para el gráfico circular
  List<PieChartSectionData> _getMockPieData() {
    final colorScheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;
    
    return [
      PieChartSectionData(
        value: 40,
        title: '40%',
        color: colorScheme.primaryContainer,
        radius: 50,
        titleStyle: textTheme.bodySmall?.copyWith(fontWeight: FontWeight.bold)
      ),
      PieChartSectionData(
        value: 30,
        title: '30%',
        color: colorScheme.secondaryContainer,
        radius: 50,
        titleStyle: textTheme.bodySmall?.copyWith(fontWeight: FontWeight.bold)
      ),
      PieChartSectionData(
        value: 30,
        title: '30%',
        color: colorScheme.tertiaryContainer,
        radius: 50,
        titleStyle: textTheme.bodySmall?.copyWith(fontWeight: FontWeight.bold)
      ),
    ];
  }
}


// --- (Widget _SummaryCard sin cambios) ---
class _SummaryCard extends StatelessWidget {
  // ... (código idéntico al anterior)
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _SummaryCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0.5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      color: theme.colorScheme.surfaceContainerHighest,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Icon(icon, size: 32, color: color),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                Text(
                  value,
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}