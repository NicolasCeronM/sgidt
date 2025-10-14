import 'package:flutter/material.dart';
import 'package:flutter_cached_pdfview/flutter_cached_pdfview.dart';
import 'package:url_launcher/url_launcher.dart';

class DocumentViewer extends StatelessWidget {
  final String url;
  final double? height;
  final BorderRadius? borderRadius;

  const DocumentViewer({
    super.key,
    required this.url,
    this.height,
    this.borderRadius,
  });

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

  @override
  Widget build(BuildContext context) {
    final radius = borderRadius ?? BorderRadius.circular(16);
    final h = height ?? 420;

    Widget child;

    if (_isPdf) {
      child = const PDF().cachedFromUrl(
        // URL del PDF
        // Puedes pasar headers si tu API los requiere:
        // url, headers: {'Authorization': 'Bearer ...'}
        // En tu caso el archivo está bajo /media y es público.
        // ignore: invalid_use_of_visible_for_testing_member
        '', // <- será reemplazado debajo, ver Builder
        placeholder: (progress) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              const SizedBox(height: 12),
              Text('Cargando PDF… $progress%'),
            ],
          ),
        ),
        errorWidget: (error) => _ErrorBox(
          title: 'No se pudo cargar el PDF',
          details: '$error',
          url: url,
        ),
      );
      // Trick: necesitamos inyectar la URL real en runtime porque el constructor const
      // no acepta parámetros dinámicos. Usamos Builder para recrear el widget con la url.
      child = Builder(
        builder: (_) => PDF().cachedFromUrl(
          url,
          placeholder: (progress) => Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircularProgressIndicator(),
                const SizedBox(height: 12),
                Text('Cargando PDF… $progress%'),
              ],
            ),
          ),
          errorWidget: (error) => _ErrorBox(
            title: 'No se pudo cargar el PDF',
            details: '$error',
            url: url,
          ),
        ),
      );
    } else if (_isImage) {
      child = InteractiveViewer(
        minScale: 0.5,
        maxScale: 5,
        child: Image.network(
          url,
          fit: BoxFit.contain,
          loadingBuilder: (context, child, evt) {
            if (evt == null) return child;
            final expected = evt.expectedTotalBytes ?? 0;
            final loaded = evt.cumulativeBytesLoaded;
            final progress =
                expected > 0 ? (loaded / expected * 100).toStringAsFixed(0) : '?';
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 12),
                  Text('Cargando imagen… $progress%'),
                ],
              ),
            );
          },
          errorBuilder: (context, error, stack) {
            return _ErrorBox(
              title: 'No se pudo cargar la imagen',
              details: '$error',
              url: url,
            );
          },
        ),
      );
    } else {
      // Desconocido: ofrecer abrir/descargar
      child = Center(
        child: _OpenExternal(url: url),
      );
    }

    return ClipRRect(
      borderRadius: radius,
      child: Container(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        height: h,
        width: double.infinity,
        child: child,
      ),
    );
  }
}

class _OpenExternal extends StatelessWidget {
  final String url;
  const _OpenExternal({required this.url});

  Future<void> _open() async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.open_in_new, size: 42),
        const SizedBox(height: 12),
        const Text('Formato no soportado para vista previa'),
        const SizedBox(height: 8),
        FilledButton.icon(
          onPressed: _open,
          icon: const Icon(Icons.download),
          label: const Text('Abrir / Descargar'),
        ),
      ],
    );
  }
}

class _ErrorBox extends StatelessWidget {
  final String title;
  final String details;
  final String url;
  const _ErrorBox({
    required this.title,
    required this.details,
    required this.url,
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
          _OpenExternal(url: url),
        ],
      ),
    );
  }
}
