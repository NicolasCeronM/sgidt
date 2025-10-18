import 'package:flutter/material.dart';
import 'documentos_screen.dart'; // Para navegar a la lista de documentos
import '../services/documents_service.dart';
import '../theme/theme_controller.dart'; // <-- 1. Importa el controlador del tema

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = true;
  List<Map<String, String>> _recentDocs = [];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final allDocs = await DocumentsService.fetchRecent();
      if (mounted) {
        setState(() {
          _recentDocs = allDocs.take(3).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudieron cargar los documentos recientes.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;

    // --- 2. Lógica para el botón del tema ---
    final IconData themeIcon;
    final String themeTooltip;
    switch (ThemeController.instance.mode) {
      case ThemeMode.light:
        themeIcon = Icons.light_mode_outlined;
        themeTooltip = 'Cambiar a modo oscuro';
        break;
      case ThemeMode.dark:
        themeIcon = Icons.dark_mode_outlined;
        themeTooltip = 'Usar tema del sistema';
        break;
      case ThemeMode.system:
        themeIcon = Icons.brightness_auto_outlined;
        themeTooltip = 'Cambiar a modo claro';
        break;
    }
    // --------------------------------------------------------------------

    return Scaffold(
      appBar: AppBar(
        title: const Text('SGIDT - Inicio'),
        centerTitle: true,
        actions: [
          // --- 3. El IconButton para cambiar el tema ---
          IconButton(
            onPressed: () {
              ThemeController.instance.cycleTheme();
            },
            icon: Icon(themeIcon),
            tooltip: themeTooltip,
          ),
          // ---------------------------------------------
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            // Saludo Personalizado
            Text(
              'Bienvenido de vuelta, Benjamín',
              style: textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Aquí tienes un resumen de tu actividad.',
              style: textTheme.bodyLarge?.copyWith(color: theme.colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 24),

            // Sección de Menú
            _MenuCard(
              icon: Icons.folder_copy_outlined,
              title: 'Mis Documentos',
              subtitle: 'Revisa todas tus facturas y archivos',
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const DocumentosScreen()),
                );
              },
            ),
            const SizedBox(height: 16),
            _MenuCard(
              icon: Icons.bar_chart_outlined,
              title: 'Reportes',
              subtitle: 'Analiza tus datos y gastos mensuales',
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('La sección de Reportes estará disponible próximamente.'),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              },
            ),
            const SizedBox(height: 32),

            // Sección de Documentos Recientes
            Text(
              'Actividad Reciente',
              style: textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            _buildRecentDocs(),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentDocs() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_recentDocs.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 24.0),
          child: Text('No hay documentos recientes para mostrar.'),
        ),
      );
    }

    return Column(
      children: _recentDocs.map((doc) {
        final proveedor = doc['proveedor'] ?? doc['emisor'] ?? 'Proveedor Desconocido';
        final total = doc['total'] ?? doc['monto'] ?? 'S/I';
        final estado = doc['estado'] ?? 'Pendiente';
        return _RecentDocTile(
          proveedor: proveedor,
          total: total,
          estado: estado,
        );
      }).toList(),
    );
  }
}


// --- WIDGETS PERSONALIZADOS ---

class _MenuCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _MenuCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0.5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Row(
            children: [
              Icon(icon, size: 40, color: theme.colorScheme.primary),
              const SizedBox(width: 20),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: theme.textTheme.titleLarge),
                    const SizedBox(height: 4),
                    Text(subtitle, style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios_rounded, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}

class _RecentDocTile extends StatelessWidget {
  final String proveedor;
  final String total;
  final String estado;

  const _RecentDocTile({
    required this.proveedor,
    required this.total,
    required this.estado,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: theme.dividerColor, width: 0.5),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Icon(Icons.receipt_long_outlined, color: theme.colorScheme.secondary),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(proveedor, style: theme.textTheme.titleMedium, overflow: TextOverflow.ellipsis),
                  Text('Total: $total', style: theme.textTheme.bodySmall),
                ],
              ),
            ),
            const SizedBox(width: 16),
            Chip(
              label: Text(estado),
              labelStyle: TextStyle(fontSize: 12, color: theme.colorScheme.onSecondaryContainer),
              backgroundColor: theme.colorScheme.secondaryContainer,
              side: BorderSide.none,
              padding: const EdgeInsets.symmetric(horizontal: 8),
            ),
          ],
        ),
      ),
    );
  }
}