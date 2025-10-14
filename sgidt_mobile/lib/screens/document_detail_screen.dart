import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:url_launcher/url_launcher.dart';

class DocumentDetailScreen extends StatelessWidget {
  final Map<String, String> documento;
  const DocumentDetailScreen({super.key, required this.documento});

  String _val(String key) => (documento[key] ?? '').toString();

  @override
  Widget build(BuildContext context) {
    final urlArchivo = _val('archivo');

    return Scaffold(
      appBar: AppBar(
        title: Text('Documento #${_val('folio')}'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _InfoChipRow(
            estado: _val('estado'),
            siiEstado: _val('sii_estado'),
            validado: (_val('validado_sii').toLowerCase() == 'true'),
          ),
          const SizedBox(height: 12),

          _Tile(label: 'Tipo', value: _val('tipo_documento')),
          _Tile(label: 'Folio', value: _val('folio')),
          _Tile(label: 'Proveedor', value: _val('razon_social_proveedor')),
          _Tile(label: 'RUT', value: _val('rut_proveedor')),
          _Tile(label: 'Fecha emisión', value: _val('fecha_emision')),
          _Tile(label: 'Neto', value: _val('monto_neto')),
          _Tile(label: 'Exento', value: _val('monto_exento')),
          _Tile(label: 'IVA', value: _val('iva')),
          _Tile(label: 'Total', value: _val('total')),
          if (_val('sii_track_id').isNotEmpty)
            _Tile(label: 'SII Track ID', value: _val('sii_track_id')),
          if (_val('sii_glosa').isNotEmpty)
            _Tile(label: 'SII Glosa', value: _val('sii_glosa')),
          const SizedBox(height: 16),

          Text('Archivo', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          if (urlArchivo.isNotEmpty)
            _DocumentViewer(url: urlArchivo, height: 520)
          else
            const Text('— No hay archivo disponible —'),
        ],
      ),
    );
  }
}

class _Tile extends StatelessWidget {
  final String label;
  final String value;
  const _Tile({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      contentPadding: EdgeInsets.zero,
      title: Text(label, style: Theme.of(context).textTheme.bodySmall),
      subtitle: Text(
        value.isEmpty ? '—' : value,
        style: Theme.of(context).textTheme.titleMedium,
      ),
    );
  }
}

class _InfoChipRow extends StatelessWidget {
  final String estado;
  final String siiEstado;
  final bool validado;

  const _InfoChipRow({
    required this.estado,
    required this.siiEstado,
    required this.validado,
  });

  Color _chipColor() {
    if (validado) return Colors.green;
    if (estado.toLowerCase() == 'procesado') return Colors.blue;
    return Colors.orange;
  }

  @override
  Widget build(BuildContext context) {
    final color = _chipColor();
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        Chip(
          label: Text('Estado: $estado'),
          backgroundColor: color.withOpacity(0.15),
          side: BorderSide(color: color.withOpacity(0.4)),
        ),
        Chip(
          label: Text('SII: $siiEstado'),
          backgroundColor: color.withOpacity(0.15),
          side: BorderSide(color: color.withOpacity(0.4)),
        ),
        Chip(
          label: Text(validado ? 'Validado SII' : 'No validado'),
          backgroundColor:
              (validado ? Colors.green : Colors.red).withOpacity(0.15),
          side: BorderSide(
            color: (validado ? Colors.green : Colors.red).withOpacity(0.4),
          ),
        ),
      ],
    );
  }
}

/// Visor con vista previa inline:
/// - JPG/PNG: embebido con zoom.
/// - PDF:
///   - En Web: se muestra tarjeta con botón "Abrir PDF" (nueva pestaña).
///   - En App nativa (Android/iOS/Desktop): también botón externo (simple y estable).
class _DocumentViewer extends StatelessWidget {
  final String url;
  final double height;
  const _DocumentViewer({required this.url, this.height = 420, super.key});

  String _ext(String u) {
    final path = Uri.parse(u).path.toLowerCase();
    final dot = path.lastIndexOf('.');
    if (dot == -1) return '';
    return path.substring(dot + 1);
  }

  bool get _isImage {
    final e = _ext(url);
    return e == 'jpg' || e == 'jpeg' || e == 'png';
  }

  bool get _isPdf => _ext(url) == 'pdf';

  Future<void> _openExternal({bool newTab = false}) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(
        uri,
        mode: kIsWeb
            ? LaunchMode.externalApplication
            : LaunchMode.inAppBrowserView,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(16);

    Widget child;
    if (_isImage) {
      // === IMÁGENES ===
      child = InteractiveViewer(
        minScale: 0.5,
        maxScale: 5,
        child: Image.network(
          url,
          fit: BoxFit.contain,
          loadingBuilder: (context, child, evt) {
            if (evt == null) return child;
            return const Center(child: CircularProgressIndicator());
          },
          errorBuilder: (context, error, stack) {
            return _ErrorBox(
              title: 'No se pudo cargar la imagen',
              details: '$error',
              onOpen: _openExternal,
              cta: 'Abrir imagen',
            );
          },
        ),
      );
    } else if (_isPdf) {
      // === PDF (Web y Nativo): abrimos externo para máxima compatibilidad ===
      child = Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.picture_as_pdf, size: 48),
            const SizedBox(height: 12),
            const Text('Vista previa PDF'),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed: _openExternal,
              icon: const Icon(Icons.open_in_new),
              label: const Text('Abrir PDF'),
            ),
          ],
        ),
      );
    } else {
      // === FORMATO DESCONOCIDO ===
      child = Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.insert_drive_file, size: 42),
            const SizedBox(height: 12),
            const Text('Vista previa no disponible'),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed: _openExternal,
              icon: const Icon(Icons.open_in_new),
              label: const Text('Abrir / Descargar'),
            ),
          ],
        ),
      );
    }

    return ClipRRect(
      borderRadius: radius,
      child: Container(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        height: height,
        width: double.infinity,
        child: child,
      ),
    );
  }
}

class _ErrorBox extends StatelessWidget {
  final String title;
  final String details;
  final Future<void> Function({bool newTab}) onOpen;
  final String cta;
  const _ErrorBox({
    required this.title,
    required this.details,
    required this.onOpen,
    this.cta = 'Abrir / Descargar',
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(18),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 42),
          const SizedBox(height: 12),
          Text(title, textAlign: TextAlign.center),
          const SizedBox(height: 8),
          Text(
            details,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: () => onOpen(newTab: kIsWeb),
            icon: const Icon(Icons.open_in_new),
            label: Text(cta),
          ),
        ],
      ),
    );
  }
}
