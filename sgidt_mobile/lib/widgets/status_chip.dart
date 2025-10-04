import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class StatusChip extends StatelessWidget {
  final String status; // 'validado' | 'pendiente' | 'rechazado'
  const StatusChip(this.status, {super.key});

  @override
  Widget build(BuildContext context) {
    Color bg = Colors.grey.shade200;
    Color fg = Colors.grey.shade800;
    if (status == 'validado') { bg = AppTheme.ok.withOpacity(.15); fg = AppTheme.ok; }
    if (status == 'rechazado') { bg = AppTheme.err.withOpacity(.15); fg = AppTheme.err; }
    if (status == 'pendiente') { bg = Colors.amber.withOpacity(.18); fg = Colors.amber.shade800; }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Text(status[0].toUpperCase()+status.substring(1),
        style: TextStyle(fontWeight: FontWeight.w600, color: fg)),
    );
  }
}
