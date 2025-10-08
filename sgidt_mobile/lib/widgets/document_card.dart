import 'dart:ui' show FontFeature;
import 'package:flutter/material.dart';
import 'status_chip.dart';

class DocumentCard extends StatelessWidget {
  final String id;
  final String proveedor;
  final String fecha;
  final String total;   // string ya formateado o crudo
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
    final theme = Theme.of(context);

    return Card(
      elevation: 0.3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Icono
              CircleAvatar(
                radius: 24,
                backgroundColor: theme.colorScheme.primary.withOpacity(.10),
                child: Icon(Icons.receipt_long,
                    color: theme.colorScheme.primary),
              ),
              const SizedBox(width: 12),

              // Texto principal
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Proveedor (una línea, elipsis)
                    Text(
                      proveedor.isEmpty ? '—' : proveedor,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 4),
                    // Fecha
                    Text(
                      fecha,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 12),

              // Monto + Chip (sin overflow)
              Column(
                mainAxisSize: MainAxisSize.min, // 👈 evita pedir más alto
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  // Monto encogible si es largo
                  ConstrainedBox(
                    constraints:
                        const BoxConstraints(minWidth: 72, maxWidth: 120),
                    child: FittedBox(
                      alignment: Alignment.centerRight,
                      fit: BoxFit.scaleDown,
                      child: Text(
                        total,
                        textAlign: TextAlign.right,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                          fontFeatures: const [FontFeature.tabularFigures()],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  // Chip de estado
                  StatusChip(estado),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
