import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../widgets/document_card.dart';
import '../widgets/empty_state.dart';
import '../services/documents_service.dart';
import 'main_screen.dart'; // Importamos esto para usar los widgets de navegación

class DocumentosScreen extends StatefulWidget {
  const DocumentosScreen({super.key});
  @override
  State<DocumentosScreen> createState() => _DocumentosScreenState();
}

class _DocumentosScreenState extends State<DocumentosScreen> {
  int tab = 0;
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
        centerTitle: false,
        elevation: 0,
      ),
      // --- AÑADIDO EL REFRESHINDICATOR ---
      body: RefreshIndicator(
        onRefresh: _load, // <--- Conectado a tu función _load
        child: SafeArea(
          child: _buildDocs()
        ),
      ),
      // -----------------------------------
      floatingActionButton: CaptureFab(onPressed: _goCapture),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      bottomNavigationBar: CurvedBottomNav(
        index: tab,
        onTap: (i) {
          if (i == 0) {
            Navigator.pop(context); // Vuelve a la pantalla anterior (MainScreen)
            return;
          }
          if (i == 2) {
            Navigator.pushNamed(context, '/profile');
            return;
          }
          setState(() => tab = i);
        },
        onCentralTap: _goCapture,
        bgColor: scheme.surface,
        activeColor: scheme.primary,
      ),
    );
  }

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
      // --- MODIFICADO PARA PERMITIR REFRESH AÚN VACÍO ---
      // Se envuelve en un ListView para que el RefreshIndicator funcione.
      return ListView(
        children: [
          // Añadimos un Sizedbox para que el contenido no quede pegado arriba
          SizedBox(height: MediaQuery.of(context).size.height * 0.2), 
          EmptyState(
            icon: Icons.receipt_long_outlined,
            title: 'Sin documentos',
            subtitle: 'Toma una foto y envíala a SGIDT para empezar.',
            action: FilledButton.icon(
              onPressed: _goCapture,
              icon: const Icon(Icons.camera_alt),
              label: const Text('Tomar foto'),
            ),
          ),
        ],
      );
      // ----------------------------------------------------
    }
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
      itemCount: docs.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (_, i) {
        final d = docs[i];
        final id = d['id'] ?? d['uuid'] ?? d['pk'] ?? '';
        final proveedor = _pickFirst(d, ['proveedor', 'prov', 'supplier', 'emisor', 'emisor_nombre', 'emisor_razon_social', 'razon_social_emisor', 'razon_social', 'receptor', 'company', 'nombre',]) ??
            [
              _pickFirst(d, ['tipo', 'document_type', 'tipo_dte']),
              _pickFirst(d, ['folio', 'numero', 'nro']),
            ].whereType<String>().join(' #');
        final fecha = _pickFirst(d, ['fecha', 'fecha_emision', 'fecha_recepcion', 'created', 'created_at', 'date',]) ?? '';
        final totalRaw = d['total'] ?? d['monto'] ?? d['amount'] ?? '';
        final total = _formatAmountCLP(totalRaw);
        final estado = _pickFirst(d, ['estado', 'status', 'estado_desc', 'resultado', 'status_label',]) ?? '—';
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

  static String _formatAmountCLP(dynamic v) {
    final n = _parseAmountSmart(v);
    if (n == null) return (v ?? '').toString();
    return _formatCLP(n);
  }

  static num? _parseAmountSmart(dynamic v) {
    if (v == null) return null;
    if (v is num) return v;
    String s = v.toString().trim();
    if (s.isEmpty) return null;
    s = s.replaceAll(RegExp(r'[^\d,.\-]'), '');
    final hasDot = s.contains('.');
    final hasComma = s.contains(',');
    if (hasDot && hasComma) {
      s = s.replaceAll('.', '').replaceAll(',', '.');
    } else if (hasComma && !hasDot) {
      s = s.replaceAll(',', '.');
    } else if (hasDot && !hasComma) {
      final dotCount = '.'.allMatches(s).length;
      final last = s.lastIndexOf('.');
      final digitsRight = s.length - last - 1;
      final looksThousands = dotCount > 1 || digitsRight == 3;
      if (looksThousands) {
        s = s.replaceAll('.', '');
      }
    }
    return num.tryParse(s);
  }

  static String _formatCLP(num value) {
    final s = value.toStringAsFixed(0);
    final buf = StringBuffer();
    for (int i = 0; i < s.length; i++) {
      final idx = s.length - 1 - i;
      buf.write(s[idx]);
      if (i % 3 == 2 && idx != 0) buf.write('.');
    }
    final miles = buf.toString().split('').reversed.join();
    return '\$$miles';
  }
}