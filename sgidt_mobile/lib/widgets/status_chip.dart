import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class StatusChip extends StatelessWidget {
  final String status;
  const StatusChip(this.status, {super.key});

  @override
  Widget build(BuildContext context) {
    final s = (status).trim().toLowerCase();

    Color fg;
    if (s.contains('valid') || s.contains('proces')) {
      fg = AppTheme.ok;
    } else if (s.contains('rechaz') || s.contains('error') || s.contains('fail')) {
      fg = AppTheme.err;
    } else {
      fg = Theme.of(context).colorScheme.primary;
    }
    final bg = fg.withOpacity(.15);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        _pretty(status),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          color: fg,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  String _pretty(String v) {
    if (v.isEmpty) return '—';
    final t = v.trim();
    return t[0].toUpperCase() + t.substring(1).toLowerCase();
  }
}
