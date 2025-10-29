import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:fl_chart/fl_chart.dart';

import '../services/reportes_service.dart';
import '../core/api/api_result.dart';

class ReportesScreen extends StatefulWidget {
  const ReportesScreen({super.key});

  @override
  State<ReportesScreen> createState() => _ReportesScreenState();
}

class _ReportesScreenState extends State<ReportesScreen> {
  bool _isLoading = true;
  String? _error;

  // Estado para los datos de la API
  String _totalIngresos = "-\$";
  String _totalGastos = "-\$";
  String _resultadoMes = "-\$";

  late DateTime _selectedDate;
  String _textoPeriodo = "Cargando...";

  List<BarChartGroupData> _barChartData = [];
  List<PieChartSectionData> _pieChartData = [];
  final List<Color> _pieColors = [
    Colors.blue.shade400,
    Colors.green.shade400,
    Colors.orange.shade400,
    Colors.purple.shade400,
    Colors.red.shade400,
    Colors.teal.shade400,
  ];

  @override
  void initState() {
    super.initState();
    initializeDateFormatting('es');
    _selectedDate = DateTime.now();
    _updatePeriodoText();
    _loadData();
  }

  void _updatePeriodoText() {
    _textoPeriodo = DateFormat('MMMM yyyy', 'es').format(_selectedDate);
  }

  /// Carga los datos desde el servicio de reportes.
  Future<void> _loadData() async {
    if (!_isLoading) {
      setState(() => _isLoading = true);
    }
    setState(() => _error = null);

    final result = await ReportesService.instance.getReportData(
      year: _selectedDate.year,
      month: _selectedDate.month,
    );

    if (!mounted) return;

    if (result is Success<Map<String, dynamic>>) {
      _updateUIWithData(result.data);
    } else if (result is Failure) {
      setState(() {
        _error = result.toString();
        _isLoading = false;
      });
    }
  }

  /// Actualiza el estado de la UI con los datos de la API.
  void _updateUIWithData(Map<String, dynamic> data) {
    final kpis = data['kpis'] as Map<String, dynamic>? ?? {};
    final charts = data['charts'] as Map<String, dynamic>? ?? {};

    final currencyFormat = NumberFormat.currency(
      locale: 'es_CL',
      symbol: '\$',
      decimalDigits: 0,
    );

    setState(() {
      // Actualiza los KPIs
      _totalIngresos = currencyFormat.format(kpis['total_ingresos'] ?? 0);
      _totalGastos = currencyFormat.format(kpis['total_gastos'] ?? 0);
      _resultadoMes = currencyFormat.format(kpis['resultado_mes'] ?? 0);

      // Actualiza datos del gráfico de barras (Ingresos vs Gastos)
      final ingresosData = (kpis['total_ingresos'] ?? 0).toDouble();
      final gastosData = (kpis['total_gastos'] ?? 0).toDouble();
      _barChartData = _createBarChartData(ingresosData, gastosData);

      // Actualiza datos del gráfico circular (Distribución de Ingresos)
      final distribucionIngresos = charts['distribucion_ingresos'] as Map<String, dynamic>? ?? {};
      _pieChartData = _createPieChartData(distribucionIngresos);

      _isLoading = false;
    });
  }

  /// Muestra el selector de fecha (mes y año).
  Future<void> _seleccionarPeriodo() async {
    final DateTime? newDate = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      locale: const Locale('es'),
      initialDatePickerMode: DatePickerMode.year,
    );

    if (newDate != null && (newDate.month != _selectedDate.month || newDate.year != _selectedDate.year)) {
      setState(() {
        _selectedDate = newDate;
        _updatePeriodoText();
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

  /// Construye el cuerpo principal con los datos del reporte.
  Widget _buildReportBody() {
    final textTheme = Theme.of(context).textTheme;
    final colorScheme = Theme.of(context).colorScheme;

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16.0),
      children: [
        // Selector de Período
        _buildPeriodoSelector(colorScheme),
        const SizedBox(height: 20),

        // Tarjetas de Resumen (KPIs)
        _buildKpiGrid(colorScheme),
        const SizedBox(height: 32),

        // Sección de Gráficos
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

  // --- WIDGETS AUXILIARES (AQUÍ ESTABA EL ERROR) ---

  Widget _buildPeriodoSelector(ColorScheme colorScheme) {
    return Card(
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
    );
  }

  Widget _buildKpiGrid(ColorScheme colorScheme) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.1,
      children: [
        _SummaryCard(
          title: "Total Ingresos",
          value: _totalIngresos,
          icon: Icons.arrow_upward_rounded,
          color: Colors.green.shade600,
        ),
        _SummaryCard(
          title: "Total Gastos",
          value: _totalGastos,
          icon: Icons.arrow_downward_rounded,
          color: colorScheme.error,
        ),
        _SummaryCard(
          title: "Resultado del Mes",
          value: _resultadoMes,
          icon: Icons.account_balance_wallet_outlined,
          color: colorScheme.primary,
        ),
      ],
    );
  }

  Widget _buildBarChart(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Ingresos vs Gastos", style: textTheme.titleMedium),
        const SizedBox(height: 16),
        SizedBox(
          height: 200,
          child: BarChart(
            BarChartData(
              alignment: BarChartAlignment.spaceAround,
              barTouchData: BarTouchData(enabled: true),
              borderData: FlBorderData(show: false),
              gridData: const FlGridData(show: false),
              titlesData: FlTitlesData(
                show: true,
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (double value, TitleMeta meta) {
                      String text = '';
                      switch (value.toInt()) {
                        case 0: text = 'Ingresos'; break;
                        case 1: text = 'Gastos'; break;
                      }
                      return Padding(
                        padding: const EdgeInsets.only(top: 8.0),
                        child: Text(text, style: textTheme.bodySmall),
                      );
                    },
                    reservedSize: 30,
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 50,
                    getTitlesWidget: (value, meta) {
                      if (value == 0) return const Text('');
                      return Text('${(value / 1000).round()}k', style: textTheme.bodySmall);
                    },
                  ),
                ),
              ),
              barGroups: _barChartData,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPieChart(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Distribución de Ingresos", style: textTheme.titleMedium),
        const SizedBox(height: 16),
        if (_pieChartData.isEmpty)
          const Center(child: Padding(
            padding: EdgeInsets.symmetric(vertical: 40.0),
            child: Text("Sin datos de ingresos para este período."),
          ))
        else
          SizedBox(
            height: 200,
            child: PieChart(
              PieChartData(
                sections: _pieChartData,
                centerSpaceRadius: 60,
                sectionsSpace: 2,
                pieTouchData: PieTouchData(enabled: true),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildErrorBody(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.cloud_off_outlined, size: 60, color: Theme.of(context).colorScheme.error),
            const SizedBox(height: 16),
            Text('Ocurrió un error', style: Theme.of(context).textTheme.headlineSmall, textAlign: TextAlign.center),
            const SizedBox(height: 8),
            Text(error, style: Theme.of(context).textTheme.bodyMedium, textAlign: TextAlign.center),
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

  // --- FUNCIONES DE DATOS PARA GRÁFICOS (AQUÍ ESTABA EL ERROR) ---

  List<BarChartGroupData> _createBarChartData(double ingresos, double gastos) {
    return [
      _makeBarGroup(0, ingresos, Colors.green.shade600),
      _makeBarGroup(1, gastos, Theme.of(context).colorScheme.error),
    ];
  }

  BarChartGroupData _makeBarGroup(int x, double y, Color color) {
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: y,
          color: color,
          width: 32,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(6),
            topRight: Radius.circular(6),
          ),
        ),
      ],
    );
  }

  List<PieChartSectionData> _createPieChartData(Map<String, dynamic> data) {
    final List<PieChartSectionData> sections = [];
    int colorIndex = 0;
    
    final total = data.values.fold(0.0, (sum, item) => sum + (item as num));
    if (total == 0) return [];

    data.forEach((key, value) {
      final percentage = (value / total) * 100;
      sections.add(
        PieChartSectionData(
          value: value.toDouble(),
          title: '${percentage.toStringAsFixed(0)}%',
          color: _pieColors[colorIndex % _pieColors.length],
          radius: 50,
          titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
        )
      );
      colorIndex++;
    });

    return sections;
  }
}

// --- WIDGET DE TARJETA DE RESUMEN ---

class _SummaryCard extends StatelessWidget {
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
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}