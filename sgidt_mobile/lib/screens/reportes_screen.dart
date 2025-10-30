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

  // KPIs
  String _totalIngresos = "-\$";
  String _totalGastos = "-\$";
  String _resultadoMes = "-\$";

  late DateTime _selectedDate;
  String _textoPeriodo = "Cargando...";

  // Charts data
  List<BarChartGroupData> _barChartData = [];
  List<PieChartSectionData> _pieChartData = [];
  Map<String, double> _pieMap = {}; // para leyenda

  // Nuevos: tendencia (line) y categorias (bars)
  List<FlSpot> _lineSpots = [];
  List<BarChartGroupData> _categoryBarGroups = [];
  List<String> _categoryNames = [];

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

  Future<void> _loadData() async {
    if (!_isLoading) setState(() => _isLoading = true);
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

  void _updateUIWithData(Map<String, dynamic> data) {
    final kpis = data['kpis'] as Map<String, dynamic>? ?? {};
    final charts = data['charts'] as Map<String, dynamic>? ?? {};

    final currencyFormat = NumberFormat.currency(
      locale: 'es_CL',
      symbol: '\$',
      decimalDigits: 0,
    );

    setState(() {
      // KPIs
      _totalIngresos = currencyFormat.format(kpis['total_ingresos'] ?? 0);
      _totalGastos = currencyFormat.format(kpis['total_gastos'] ?? 0);
      _resultadoMes = currencyFormat.format(kpis['resultado_mes'] ?? 0);

      // Bar simple (ingresos vs gastos)
      final ingresosData = (kpis['total_ingresos'] ?? 0).toDouble();
      final gastosData = (kpis['total_gastos'] ?? 0).toDouble();
      _barChartData = _createBarChartData(ingresosData, gastosData);

      // Pie (distribución de ingresos)
      final distribucionIngresos = charts['distribucion_ingresos'] as Map<String, dynamic>? ?? {};
      _pieMap = distribucionIngresos.map((k, v) => MapEntry(k, (v as num).toDouble()));
      _pieChartData = _createPieChartData(_pieMap);

      // Line (tendencia). Espera una lista de números: charts['tendencia'] = [..]
      _lineSpots = [];
      final tendencia = charts['tendencia'] as List<dynamic>? ?? [];
      for (var i = 0; i < tendencia.length; i++) {
        final val = (tendencia[i] is num) ? (tendencia[i] as num).toDouble() : 0.0;
        _lineSpots.add(FlSpot(i.toDouble(), val));
      }

      // Categorías para barras: charts['gastos_categorias'] -> Map<String, number>
      final catMap = charts['gastos_categorias'] as Map<String, dynamic>? ?? {};
      _categoryNames = catMap.keys.toList();
      _categoryBarGroups = [];
      for (var i = 0; i < _categoryNames.length; i++) {
        final key = _categoryNames[i];
        final v = (catMap[key] as num).toDouble();
        _categoryBarGroups.add(_makeBarGroup(i, v, _pieColors[i % _pieColors.length]));
      }

      _isLoading = false;
    });
  }

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

  // UI
  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('SGIDT - Reportes'),
        centerTitle: true,
        actions: [
          IconButton(
            tooltip: 'Seleccionar periodo',
            icon: const Icon(Icons.calendar_today_outlined),
            onPressed: _seleccionarPeriodo,
          ),
          IconButton(
            tooltip: 'Refrescar',
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 250),
          child: _isLoading
              ? Container(
                  key: const ValueKey('loading'),
                  alignment: Alignment.center,
                  padding: const EdgeInsets.all(24),
                  child: const CircularProgressIndicator(),
                )
              : _error != null
                  ? _buildErrorBody(_error!)
                  : _buildReportBody(colorScheme),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _seleccionarPeriodo,
        icon: const Icon(Icons.date_range),
        label: Text(_textoPeriodo),
      ),
    );
  }

  Widget _buildReportBody(ColorScheme colorScheme) {
    final textTheme = Theme.of(context).textTheme;
    return ListView(
      padding: const EdgeInsets.all(16),
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        // Header con periodo y quick actions
        Row(
          children: [
            Expanded(
              child: Card(
                elevation: 0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: ListTile(
                  leading: const Icon(Icons.calendar_month_outlined),
                  title: const Text('Período'),
                  subtitle: Text(_textoPeriodo, style: const TextStyle(fontWeight: FontWeight.w600)),
                  trailing: TextButton(
                    onPressed: _seleccionarPeriodo,
                    child: const Text('Cambiar'),
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // KPI Row responsivo
        LayoutBuilder(builder: (context, constraints) {
          final isWide = constraints.maxWidth > 700;
          return Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              SizedBox(
                width: isWide ? (constraints.maxWidth - 24) / 3 : constraints.maxWidth,
                child: _SummaryCard(
                  title: "Total Ingresos",
                  value: _totalIngresos,
                  icon: Icons.arrow_upward_rounded,
                  color: Colors.green.shade600,
                ),
              ),
              SizedBox(
                width: isWide ? (constraints.maxWidth - 24) / 3 : constraints.maxWidth,
                child: _SummaryCard(
                  title: "Total Gastos",
                  value: _totalGastos,
                  icon: Icons.arrow_downward_rounded,
                  color: colorScheme.error,
                ),
              ),
              SizedBox(
                width: isWide ? (constraints.maxWidth - 24) / 3 : constraints.maxWidth,
                child: _SummaryCard(
                  title: "Resultado del Mes",
                  value: _resultadoMes,
                  icon: Icons.account_balance_wallet_outlined,
                  color: colorScheme.primary,
                ),
              ),
            ],
          );
        }),
        const SizedBox(height: 20),

        // Gráficos principales: Barra y Pie
        LayoutBuilder(builder: (context, constraints) {
          final isWide = constraints.maxWidth > 900;
          if (isWide) {
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: _chartCard(child: _buildBarChart(context))),
                const SizedBox(width: 16),
                SizedBox(width: 420, child: _chartCard(child: _buildPieChart(context))),
              ],
            );
          } else {
            return Column(
              children: [
                _chartCard(child: _buildBarChart(context)),
                const SizedBox(height: 12),
                _chartCard(child: _buildPieChart(context)),
              ],
            );
          }
        }),

        const SizedBox(height: 18),

        // Gráfico de tendencia (line)
        if (_lineSpots.isNotEmpty) ...[
          _chartCard(child: _buildLineChart(context)),
          const SizedBox(height: 16),
        ],

        // Gráfico de categorías (barras por categoría)
        if (_categoryBarGroups.isNotEmpty) ...[
          _chartCard(child: _buildCategoryBars(context)),
          const SizedBox(height: 16),
        ],

        // Leyenda pie (si existe)
        if (_pieMap.isNotEmpty) ...[
          Text('Detalle de Distribución', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          _buildPieLegend(),
        ],

        const SizedBox(height: 36),
      ],
    );
  }

  Widget _chartCard({required Widget child}) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(padding: const EdgeInsets.all(16), child: child),
    );
  }

  // --- EXISTENTES: Bar chart Ingresos vs Gastos ---
  Widget _buildBarChart(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final maxValue = _barChartData.fold<double>(0.0, (prev, g) {
      final rodY = g.barRods.first.toY;
      return rodY > prev ? rodY : prev;
    });
    final double niceMax = (maxValue * 1.15).clamp(1.0, double.infinity).toDouble();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Ingresos vs Gastos", style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        SizedBox(
          height: 240,
          child: BarChart(
            BarChartData(
              maxY: niceMax,
              barTouchData: BarTouchData(
                enabled: true,
                touchTooltipData: BarTouchTooltipData(
                  getTooltipItem: (group, groupIndex, rod, rodIndex) {
                    final label = group.x == 0 ? 'Ingresos' : 'Gastos';
                    final formatted = NumberFormat.compactCurrency(locale: 'es_CL', symbol: '\$')
                        .format(rod.toY);
                    return BarTooltipItem(
                      '$label\n$formatted',
                      TextStyle(color: Theme.of(context).colorScheme.onSurface),
                    );
                  },
                ),
              ),
              titlesData: FlTitlesData(
                show: true,
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (double value, meta) {
                      final map = {0: 'Ingresos', 1: 'Gastos'};
                      final text = map[value.toInt()] ?? '';
                      return SideTitleWidget(
                        axisSide: meta.axisSide,
                        child: Text(text, style: textTheme.bodySmall),
                      );
                    },
                    reservedSize: 36,
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 60,
                    getTitlesWidget: (v, meta) {
                      final formatter = NumberFormat.compactCurrency(locale: 'es_CL', symbol: '\$');
                      if (v == 0) return const SizedBox.shrink();
                      return Text(formatter.format(v), style: textTheme.bodySmall);
                    },
                    interval: niceMax / 4,
                  ),
                ),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              gridData: FlGridData(show: true),
              borderData: FlBorderData(show: false),
              barGroups: _barChartData,
            ),
          ),
        ),
      ],
    );
  }

  // --- NUEVO: Line chart (tendencia) ---
  Widget _buildLineChart(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final maxY = _lineSpots.fold<double>(0.0, (p, s) => s.y > p ? s.y : p);
    final minY = _lineSpots.fold<double>(double.infinity, (p, s) => s.y < p ? s.y : p);
    final double top = (maxY * 1.15).toDouble();
    final double bottom = (minY * 0.85).toDouble().clamp(0.0, double.infinity);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Tendencia del periodo", style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        SizedBox(
          height: 220,
          child: LineChart(
            LineChartData(
              minY: bottom,
              maxY: top,
              lineTouchData: LineTouchData(enabled: true),
              gridData: FlGridData(show: true),
              titlesData: FlTitlesData(
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (v, meta) {
                        final formatter = NumberFormat.compactCurrency(locale: 'es_CL', symbol: '\$');
                        return Text(formatter.format(v), style: textTheme.bodySmall);
                      },
                      reservedSize: 60),
                ),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                LineChartBarData(
                  spots: _lineSpots,
                  isCurved: true,
                  barWidth: 3,
                  dotData: FlDotData(show: false),
                  belowBarData: BarAreaData(show: true, gradient: null),
                  color: Theme.of(context).colorScheme.primary,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  // --- NUEVO: Barras por categoría ---
  Widget _buildCategoryBars(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final maxValue = _categoryBarGroups.fold<double>(0.0, (prev, g) {
      final rodY = g.barRods.first.toY;
      return rodY > prev ? rodY : prev;
    });
    final double niceMax = (maxValue * 1.15).clamp(1.0, double.infinity).toDouble();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Gastos por Categoría", style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        SizedBox(
          height: (_categoryBarGroups.length * 42.0).clamp(120.0, 400.0),
          child: BarChart(
            BarChartData(
              maxY: niceMax,
              barTouchData: BarTouchData(enabled: true),
              titlesData: FlTitlesData(
                leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 80, getTitlesWidget: (v, meta) {
                  final fmt = NumberFormat.compactCurrency(locale: 'es_CL', symbol: '\$');
                  if (v == 0) return const SizedBox.shrink();
                  return Text(fmt.format(v), style: textTheme.bodySmall);
                }, interval: niceMax / 4)),
                bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              gridData: FlGridData(show: true),
              borderData: FlBorderData(show: false),
              barGroups: _categoryBarGroups,
              alignment: BarChartAlignment.spaceBetween,
            ),
          ),
        ),
        const SizedBox(height: 8),
        // Nombres de categorías debajo — si son muchas, se envuelven con Wrap
        Wrap(
          spacing: 8,
          runSpacing: 6,
          children: [
            for (var i = 0; i < _categoryNames.length; i++)
              Chip(
                avatar: Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(color: _pieColors[i % _pieColors.length], borderRadius: BorderRadius.circular(3)),
                ),
                label: Text(_categoryNames[i]),
              ),
          ],
        ),
      ],
    );
  }

  Widget _buildPieChart(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Distribución de Ingresos", style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        if (_pieChartData.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Center(child: Text("Sin datos de ingresos para este período.", style: textTheme.bodyMedium)),
          )
        else
          SizedBox(
            height: 240,
            child: Stack(
              alignment: Alignment.center,
              children: [
                PieChart(
                  PieChartData(
                    sections: _pieChartData,
                    centerSpaceRadius: 60,
                    sectionsSpace: 4,
                    pieTouchData: PieTouchData(enabled: true),
                  ),
                ),
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('Total', style: textTheme.bodySmall),
                    Text(
                      NumberFormat.currency(locale: 'es_CL', symbol: '\$', decimalDigits: 0)
                          .format(_pieMap.values.fold(0.0, (s, v) => s + v)),
                      style: textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildPieLegend() {
    final entries = _pieMap.entries.toList();
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
        child: Column(
          children: [
            for (var i = 0; i < entries.length; i++)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  children: [
                    Container(width: 18, height: 18, decoration: BoxDecoration(
                      color: _pieColors[i % _pieColors.length],
                      borderRadius: BorderRadius.circular(4),
                    )),
                    const SizedBox(width: 12),
                    Expanded(child: Text(entries[i].key, style: Theme.of(context).textTheme.bodyMedium)),
                    const SizedBox(width: 12),
                    Text(NumberFormat.currency(locale: 'es_CL', symbol: '\$', decimalDigits: 0)
                        .format(entries[i].value)),
                  ],
                ),
              ),
          ],
        ),
      ),
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

  // --- Datos para gráficos (helpers) ---

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
          width: 40,
          borderRadius: const BorderRadius.only(topLeft: Radius.circular(6), topRight: Radius.circular(6)),
        ),
      ],
    );
  }

  List<PieChartSectionData> _createPieChartData(Map<String, double> data) {
    final List<PieChartSectionData> sections = [];
    final total = data.values.fold(0.0, (sum, item) => sum + item);
    if (total == 0) return [];

    int idx = 0;
    data.forEach((key, value) {
      final percentage = (value / total) * 100;
      sections.add(PieChartSectionData(
        value: value,
        title: '${percentage.toStringAsFixed(0)}%',
        color: _pieColors[idx % _pieColors.length],
        radius: 80,
        titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
      ));
      idx++;
    });

    return sections;
  }
}

// --- Tarjeta resumen ---
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
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: theme.colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14.0, horizontal: 12.0),
        child: Row(
          children: [
            CircleAvatar(
              radius: 22,
              backgroundColor: color.withOpacity(0.12),
              child: Icon(icon, size: 22, color: color),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                  const SizedBox(height: 6),
                  Text(value, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
