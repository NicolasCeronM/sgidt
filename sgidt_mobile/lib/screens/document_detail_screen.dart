import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart'; // Importa tu tema para usar los CustomColors

class DocumentDetailScreen extends StatelessWidget {
  final Map<String, String> documento;
  const DocumentDetailScreen({super.key, required this.documento});

  // Helper para obtener valores de forma segura.
  String _val(String key) => documento[key] ?? '';

  @override
  Widget build(BuildContext context) {
    final urlArchivo = _val('archivo');
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: Text('Documento #${_val('folio')}'),
        centerTitle: false,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // --- Fila de Estados (Chips Mejorados) ---
          _InfoChipRow(
            // ✅ Le pasamos de nuevo el estado interno
            estado: _val('estado'),
            siiEstado: _val('sii_estado'),
          ),
          const SizedBox(height: 24),

          // --- Tarjeta Principal con el Total Destacado ---
          Card(
            elevation: 0.5,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _val('razon_social_proveedor').isEmpty ? 'Proveedor no especificado' : _val('razon_social_proveedor'),
                    style: textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Folio #${_val('folio')} • ${_val('fecha_emision')}',
                    style: textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
                  ),
                  const Divider(height: 32),
                  _HighlightedTotal(amount: '\$${_val('total')}'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // --- Sección de Detalles Agrupados ---
          Text('Detalles del Documento', style: textTheme.titleMedium),
          const SizedBox(height: 8),
          _DetailSection(
            children: [
              _DetailItem(label: 'Tipo Documento', value: _val('tipo_documento')),
              _DetailItem(label: 'RUT Proveedor', value: _val('rut_proveedor')),
              _DetailItem(label: 'Monto Neto', value: '\$${_val('monto_neto')}', isNumeric: true),
              _DetailItem(label: 'Monto Exento', value: '\$${_val('monto_exento')}', isNumeric: true),
              _DetailItem(label: 'IVA', value: '\$${_val('iva')}', isNumeric: true),
            ],
          ),
          const SizedBox(height: 24),

          // --- Sección SII (si existe) ---
          if (_val('sii_track_id').isNotEmpty || _val('sii_glosa').isNotEmpty) ...[
            Text('Información SII', style: textTheme.titleMedium),
            const SizedBox(height: 8),
            _DetailSection(
              children: [
                if (_val('sii_track_id').isNotEmpty)
                  _DetailItem(label: 'Track ID', value: _val('sii_track_id')),
                if (_val('sii_glosa').isNotEmpty)
                  _DetailItem(label: 'Glosa', value: _val('sii_glosa'), isMultiline: true),
              ],
            ),
            const SizedBox(height: 24),
          ],


          // --- Visor de Archivo ---
          Text('Archivo Adjunto', style: textTheme.titleMedium),
          const SizedBox(height: 8),
          if (urlArchivo.isNotEmpty)
            _DocumentViewer(url: urlArchivo, height: 250)
          else
            const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 48.0),
                child: Text('— No hay archivo disponible —'),
              ),
            ),
        ],
      ),
    );
  }
}

// --- WIDGETS DE UI REUTILIZABLES Y MEJORADOS ---

/// Contenedor estilizado para agrupar items de detalle.
class _DetailSection extends StatelessWidget {
  final List<Widget> children;
  const _DetailSection({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: children,
      ),
    );
  }
}


/// Reemplaza al antiguo _Tile. Más limpio y flexible.
class _DetailItem extends StatelessWidget {
  final String label;
  final String value;
  final bool isNumeric;
  final bool isMultiline;

  const _DetailItem({
    required this.label,
    required this.value,
    this.isNumeric = false,
    this.isMultiline = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: isMultiline ? CrossAxisAlignment.start : CrossAxisAlignment.center,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              value.isEmpty ? '—' : value,
              textAlign: isNumeric ? TextAlign.end : (isMultiline ? TextAlign.start : TextAlign.end),
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontFamily: isNumeric ? 'monospace' : null,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Widget para destacar el monto total.
class _HighlightedTotal extends StatelessWidget {
  final String amount;
  const _HighlightedTotal({required this.amount});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text('Total del Documento', style: Theme.of(context).textTheme.titleMedium),
        Text(
          amount,
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: scheme.primary,
          ),
        ),
      ],
    );
  }
}

/// ✅ Fila de Chips corregida para mostrar ambos estados.
class _InfoChipRow extends StatelessWidget {
  final String estado;
  final String siiEstado;

  const _InfoChipRow({
    required this.estado,
    required this.siiEstado,
  });

  @override
  Widget build(BuildContext context) {
    final customColors = Theme.of(context).extension<CustomColors>()!;
    final scheme = Theme.of(context).colorScheme;

    // Lógica para el Chip del estado SII
    final String siiStatusText;
    final Color siiStatusColor;
    final IconData siiStatusIcon;

    final lowerSii = siiEstado.toLowerCase();
    if (lowerSii.contains('aceptado')) {
      siiStatusText = 'Aceptado por SII';
      siiStatusColor = customColors.success!;
      siiStatusIcon = Icons.check_circle_rounded;
    } else if (lowerSii.contains('rechazado')) {
      siiStatusText = 'Rechazado por SII';
      siiStatusColor = customColors.error!;
      siiStatusIcon = Icons.cancel_rounded;
    } else {
      siiStatusText = siiEstado.isEmpty ? 'Pendiente SII' : siiEstado;
      siiStatusColor = scheme.secondary;
      siiStatusIcon = Icons.hourglass_top_rounded;
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        // Chip para el estado del SII (el más importante)
        Chip(
          avatar: Icon(siiStatusIcon, color: siiStatusColor, size: 20),
          label: Text(siiStatusText),
          labelStyle: TextStyle(color: siiStatusColor, fontWeight: FontWeight.bold),
          backgroundColor: siiStatusColor.withOpacity(0.15),
          side: BorderSide.none,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        ),
        
        // Chip para el estado interno (si existe)
        if (estado.isNotEmpty)
          Chip(
            avatar: Icon(Icons.sync_rounded, color: scheme.onSurfaceVariant, size: 20),
            label: Text('Proceso: $estado'),
            backgroundColor: scheme.surfaceContainerHighest,
            side: BorderSide.none,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          ),
      ],
    );
  }
}

// --- VISOR DE DOCUMENTOS (Sin cambios) ---
class _DocumentViewer extends StatelessWidget {
  final String url;
  final double height;
  const _DocumentViewer({required this.url, this.height = 420});

  String _ext(String u) {
    final path = Uri.parse(u).path.toLowerCase();
    final dot = path.lastIndexOf('.');
    if (dot == -1) return '';
    return path.substring(dot + 1);
  }

  bool get _isPdf => _ext(url) == 'pdf';

  Future<void> _openExternal() async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    Widget child;

    if (_isPdf) {
      child = Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.picture_as_pdf_rounded, size: 56, color: scheme.primary),
        const SizedBox(height: 16),
        Text('Documento PDF', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: _openExternal,
          icon: const Icon(Icons.open_in_new),
          label: const Text('Abrir PDF'),
        ),
      ]);
    } else {
      child = Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.insert_drive_file_rounded, size: 56, color: scheme.secondary),
        const SizedBox(height: 16),
        Text('Archivo adjunto', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: _openExternal,
          icon: const Icon(Icons.open_in_new),
          label: const Text('Abrir / Descargar'),
        ),
      ]);
    }

    return Container(
      height: height,
      width: double.infinity,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: child,
    );
  }
}