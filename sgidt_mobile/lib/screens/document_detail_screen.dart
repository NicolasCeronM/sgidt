import 'dart:ui' show FontFeature;
import 'package:flutter/material.dart';

import '../services/documents_service.dart';
import '../widgets/status_chip.dart';
import '../theme/app_theme.dart';

class DocumentDetailScreen extends StatefulWidget {
  final String id;
  const DocumentDetailScreen({super.key, required this.id});

  @override
  State<DocumentDetailScreen> createState() => _DocumentDetailScreenState();
}

class _DocumentDetailScreenState extends State<DocumentDetailScreen> {
  Map<String, String>? data;
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final d = await DocumentsService.fetchDetail(widget.id);
      if (!mounted) return;
      setState(() {
        data = d;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = 'No se pudo cargar el documento';
        loading = false;
      });
    }
  }

  String? _pick(List<String> keys) {
    final m = data ?? {};
    for (final k in keys) {
      final v = m[k];
      if (v != null && v.trim().isNotEmpty) return v.trim();
    }
    return null;
  }

  // ====== Parser + formato CLP (igual que en Home) ======

  num? _parseAmountSmart(dynamic v) {
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
      if (looksThousands) s = s.replaceAll('.', '');
    }
    return num.tryParse(s);
  }

  String _formatCLP(num value) {
    final s = value.toStringAsFixed(0);
    final b = StringBuffer();
    for (int i = 0; i < s.length; i++) {
      final idx = s.length - 1 - i;
      b.write(s[idx]);
      if (i % 3 == 2 && idx != 0) b.write('.');
    }
    return '\$${b.toString().split('').reversed.join()}';
  }

  @override
  Widget build(BuildContext context) {
    final title = 'Documento #${widget.id}';

    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: SafeArea(
        child: loading
            ? const Center(child: CircularProgressIndicator())
            : error != null
                ? _ErrorView(message: error!, onRetry: _load)
                : _buildContent(context),
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    final theme = Theme.of(context);

    final proveedor = _pick([
          'razon_social_proveedor',
          'proveedor',
          'empresa',
          'emisor_nombre',
          'emisor_razon_social',
        ]) ??
        '—';

    final fecha = _pick([
          'fecha_emision',
          'fecha',
          'creado_en',
          'created',
          'date',
        ]) ??
        '—';

    final folio = _pick([
          'folio',
          'numero',
          'nro',
          'document_number',
        ]) ??
        '—';

    final totalNum = _parseAmountSmart(_pick([
      'total',
      'monto_total',
      'monto_neto',
      'neto',
      'amount',
    ]));
    final total =
        totalNum != null ? _formatCLP(totalNum) : (_pick(['total']) ?? '—');

    final estado = _pick(['estado', 'sii_estado']) ??
        ((_pick(['validado_sii']) ?? '').toLowerCase() == 'true'
            ? 'Validado SII'
            : 'Procesado');

    final archivo = _pick(['archivo', 'file', 'url', 'document_url']) ?? '';

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      children: [
        _KV('Proveedor', proveedor),
        _KV('Fecha', fecha),
        _KV('Folio', folio),
        _KV('Total', total,
            valueStyle: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
              fontFeatures: const [FontFeature.tabularFigures()],
            )),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerLeft,
          child: StatusChip(estado),
        ),
        const SizedBox(height: 16),
        _PreviewBox(archivo: archivo),
      ],
    );
  }
}

/* -------------------- UI helpers -------------------- */

class _KV extends StatelessWidget {
  final String k;
  final String v;
  final TextStyle? valueStyle;
  const _KV(this.k, this.v, {this.valueStyle});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$k: ',
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: Text(
              v.isEmpty ? '—' : v,
              style: valueStyle ?? theme.textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }
}

class _PreviewBox extends StatelessWidget {
  final String archivo;
  const _PreviewBox({required this.archivo});

  bool get _isImage {
    final u = archivo.toLowerCase();
    return u.endsWith('.jpg') ||
        u.endsWith('.jpeg') ||
        u.endsWith('.png') ||
        u.endsWith('.webp');
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (archivo.isEmpty) {
      return _placeholder(theme, 'Sin archivo adjunto');
    }
    if (_isImage) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: AspectRatio(
          aspectRatio: 16 / 9,
          child: Image.network(
            archivo,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) =>
                _placeholder(theme, 'No se pudo cargar la imagen'),
          ),
        ),
      );
    }
    // Para PDF u otros, placeholder (sin url_launcher aquí)
    return _placeholder(theme, 'Vista previa no disponible');
  }

  Widget _placeholder(ThemeData theme, String text) {
    return Container(
      height: 180,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: theme.dividerColor),
      ),
      child: Center(
        child: Text(
          text,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.hintColor,
          ),
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 40),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
