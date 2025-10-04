import 'package:flutter/material.dart';
import '../widgets/status_chip.dart';
import '../services/documents_service.dart';

class DocumentDetailScreen extends StatelessWidget {
  final String id;
  const DocumentDetailScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Documento #$id')),
      body: FutureBuilder<Map<String, String>>(
        future: DocumentsService.fetchDetail(id),
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final d = snap.data!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const SizedBox(height: 8),
              Text('Proveedor: ${d['proveedor']}', style: const TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              Text('Fecha: ${d['fecha']}'),
              const SizedBox(height: 8),
              Text('Folio: ${d['folio']}'),
              const SizedBox(height: 8),
              Text('Total: ${d['total']}'),
              const SizedBox(height: 16),
              Align(alignment: Alignment.centerLeft, child: StatusChip(d['estado'] ?? 'pendiente')),
              const SizedBox(height: 24),
              const Placeholder(fallbackHeight: 180), // miniatura del doc (si la agregas)
            ],
          );
        },
      ),
    );
  }
}
