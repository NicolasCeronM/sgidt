import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../widgets/document_card.dart';
import '../widgets/empty_state.dart';
import '../services/documents_service.dart';
import '../theme/app_theme.dart'; // para el color rojo SGIDT

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int tab = 0; // 0 = Inicio, (1 = Capturar con FAB), 2 = Perfil
  List<Map<String, String>> docs = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final data = await DocumentsService.fetchRecent();
      // Loguea las claves del primer item para inspección rápida en consola
      if (kDebugMode && data.isNotEmpty) {
        debugPrint('🔎 Claves primer doc: ${data.first.keys.toList()}');
      }
      docs = data;
    } catch (e) {
      if (kDebugMode) debugPrint('⚠️ Error cargando documentos: $e');
      docs = [];
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  void _goCapture() => Navigator.pushNamed(context, '/capture');

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('SGIDT – Documentos'),
        centerTitle: true,
        elevation: 0,
        actions: [
          IconButton(
            onPressed: _load,
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Actualizar',
          ),
        ],
      ),

      body: SafeArea(child: _buildDocs()),

      // FAB central con notch
      floatingActionButton: CaptureFab(onPressed: _goCapture),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,

      // Barra inferior curva integrada
      bottomNavigationBar: CurvedBottomNav(
        index: tab,
        onTap: (i) {
          if (i == 2) {
            Navigator.pushNamed(context, '/profile');
            return;
          }
          setState(() => tab = i); // i == 0 (Inicio)
        },
        onCentralTap: _goCapture,
        bgColor: scheme.surface,
      ),
    );
  }

  // Helper: toma el primer campo no vacío que exista en el mapa
  String? _pickFirst(Map<String, String> m, List<String> keys) {
    for (final k in keys) {
      final v = m[k];
      if (v != null && v.trim().isNotEmpty) return v.trim();
    }
    return null;
  }

  Widget _buildDocs() {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (docs.isEmpty) {
      return EmptyState(
        icon: Icons.receipt_long_outlined,
        title: 'Sin documentos',
        subtitle: 'Toma una foto y envíala a SGIDT para empezar.',
        action: FilledButton.icon(
          onPressed: _goCapture,
          icon: const Icon(Icons.camera_alt),
          label: const Text('Tomar foto'),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 96), // deja aire sobre el FAB
      itemCount: docs.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (_, i) {
        final d = docs[i];

        final id = d['id'] ?? d['uuid'] ?? d['pk'] ?? '';

        // === proveedor/nombre ===
        final proveedor = _pickFirst(d, [
              // nombres típicos de emisor/proveedor
              'proveedor',
              'prov',
              'supplier',
              'emisor',
              'emisor_nombre',
              'emisor_razon_social',
              'razon_social_emisor',
              'razon_social',
              'receptor',
              'company',
              'nombre',
            ]) ??
            // fallback: tipo + folio si existen
            [
              _pickFirst(d, ['tipo', 'document_type', 'tipo_dte']),
              _pickFirst(d, ['folio', 'numero', 'nro']),
            ].whereType<String>().join(' #');

        // === fecha ===
        final fecha = _pickFirst(d, [
              'fecha',
              'fecha_emision',
              'fecha_recepcion',
              'created',
              'created_at',
              'date',
            ]) ??
            '';

        // === total ===
        final total = _pickFirst(d, [
              'total',
              'monto_total',
              'monto',
              'amount',
              'total_bruto',
              'total_neto',
              'neto',
            ]) ??
            '';

        // === estado ===
        final estado = _pickFirst(d, [
              'estado',
              'status',
              'estado_desc',
              'resultado',
              'status_label',
            ]) ??
            '—';

        return DocumentCard(
          id: id,
          proveedor: proveedor.isEmpty ? '—' : proveedor,
          fecha: fecha,
          total: total,
          estado: estado,
          onTap: () {
            if (id.isNotEmpty) {
              Navigator.pushNamed(context, '/document', arguments: id);
            }
          },
        );
      },
    );
  }
}

/* ============================
 *  Barra curva + FAB central
 * ============================ */

class CurvedBottomNav extends StatelessWidget {
  final int index;
  final ValueChanged<int> onTap;
  final VoidCallback onCentralTap;
  final Color bgColor;

  const CurvedBottomNav({
    super.key,
    required this.index,
    required this.onTap,
    required this.onCentralTap,
    required this.bgColor,
  });

  @override
  Widget build(BuildContext context) {
    final inactive = Theme.of(context).colorScheme.onSurface.withOpacity(.6);
    final active = AppTheme.sgidtRed;

    return BottomAppBar(
      shape: const CircularNotchedRectangle(),
      notchMargin: 8,
      color: bgColor,
      elevation: 10,
      height: 68,
      padding: EdgeInsets.zero,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _NavIcon(
            icon: Icons.home_outlined,
            isActive: index == 0,
            activeColor: active,
            inactiveColor: inactive,
            onTap: () => onTap(0),
          ),
          const SizedBox(width: 48), // espacio para el notch del FAB
          _NavIcon(
            icon: Icons.person_outline,
            isActive: index == 2,
            activeColor: active,
            inactiveColor: inactive,
            onTap: () => onTap(2),
          ),
        ],
      ),
    );
  }
}

class _NavIcon extends StatelessWidget {
  final IconData icon;
  final bool isActive;
  final Color activeColor, inactiveColor;
  final VoidCallback onTap;

  const _NavIcon({
    required this.icon,
    required this.isActive,
    required this.activeColor,
    required this.inactiveColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkResponse(
      onTap: onTap,
      radius: 28,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isActive ? activeColor.withOpacity(.10) : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Icon(icon, color: isActive ? activeColor : inactiveColor, size: 26),
      ),
    );
  }
}

class CaptureFab extends StatelessWidget {
  final VoidCallback onPressed;
  const CaptureFab({super.key, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 64,
      width: 64,
      child: FloatingActionButton(
        onPressed: onPressed,
        backgroundColor: AppTheme.sgidtRed,
        elevation: 6,
        child: const Icon(Icons.document_scanner_outlined, color: Colors.white, size: 30),
      ),
    );
  }
}
