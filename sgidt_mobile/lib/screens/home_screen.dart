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
    docs = await DocumentsService.fetchRecent();
    setState(() => loading = false);
  }

  void _goCapture() => Navigator.pushNamed(context, '/capture');

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SGIDT – Documentos'),
        actions: [
          IconButton(
            onPressed: _load,
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualizar',
          ),
        ],
      ),

      body: _buildDocs(),

      // FAB central con notch (estilo segunda imagen)
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
      ),
    );
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
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      itemCount: docs.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (_, i) {
        final d = docs[i];
        return Builder(
          builder: (context) {
            final id = d['id'] ?? '';
            // Probables alias de API: ajusta según tu backend
            final proveedor =
                d['prov'] ?? d['proveedor'] ?? d['supplier'] ?? '—';
            final fecha = d['fecha'] ?? d['created'] ?? d['date'] ?? '';
            final total = d['total'] ?? d['monto'] ?? d['amount'] ?? '';
            final estado = d['estado'] ?? d['status'] ?? '—';

            return DocumentCard(
              id: id,
              proveedor: proveedor,
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

  const CurvedBottomNav({
    super.key,
    required this.index,
    required this.onTap,
    required this.onCentralTap,
  });

  @override
  Widget build(BuildContext context) {
    final bg = Theme.of(context).colorScheme.surface;
    final inactive = Theme.of(context).colorScheme.onSurface.withOpacity(.7);
    final active = Theme.of(context).colorScheme.onSurface;

    return ClipRRect(
      borderRadius: const BorderRadius.only(
        topLeft: Radius.circular(22),
        topRight: Radius.circular(22),
      ),
      child:
          BottomAppBar
          // shape crea el notch para el FAB central
          (
            color: bg,
            elevation: 10,
            height: 64,
            shape: const CircularNotchedRectangle(),
            notchMargin: 8,
            padding: EdgeInsets.zero,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _NavIcon(
                  icon: Icons.home_outlined,
                  isActive: index == 0,
                  activeColor: active,
                  inactiveColor: inactive,
                  onTap: () => onTap(0),
                ),
                const SizedBox(width: 48), // hueco del notch del FAB
                _NavIcon(
                  icon: Icons.person_outline,
                  isActive: index == 2,
                  activeColor: active,
                  inactiveColor: inactive,
                  onTap: () => onTap(2),
                ),
              ],
            ),
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
          color: isActive
              ? AppTheme.sgidtRed.withOpacity(.10)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Icon(icon, color: isActive ? activeColor : inactiveColor),
      ),
    );
  }
}

class CaptureFab extends StatelessWidget {
  final VoidCallback onPressed;
  const CaptureFab({super.key, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton(
      onPressed: onPressed,
      backgroundColor: AppTheme.sgidtRed,
      elevation: 6,
      child: const Icon(Icons.document_scanner_outlined, color: Colors.white),
    );
  }
}
