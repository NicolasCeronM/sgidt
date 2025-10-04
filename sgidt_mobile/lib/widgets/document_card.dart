import 'package:flutter/material.dart';
import 'status_chip.dart';

class DocumentCard extends StatelessWidget {
  final String id;
  final String proveedor;
  final String fecha;
  final String total;
  final String estado;
  final VoidCallback onTap;

  const DocumentCard({
    super.key,
    required this.id,
    required this.proveedor,
    required this.fecha,
    required this.total,
    required this.estado,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0.3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.all(16),
        leading: const CircleAvatar(radius: 24, child: Icon(Icons.receipt_long)),
        title: Text(proveedor, style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text(fecha),
        trailing: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(total, style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            StatusChip(estado),
          ],
        ),
      ),
    );
  }
}
