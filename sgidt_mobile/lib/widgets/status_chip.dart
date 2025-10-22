import 'package:flutter/material.dart';
import '../theme/app_theme.dart'; // Necesitas esta importación para acceder a CustomColors

class StatusChip extends StatelessWidget {
  final String status;
  const StatusChip(this.status, {super.key});

  @override
  Widget build(BuildContext context) {
    final s = (status).trim().toLowerCase();

    // ✨ PASO 1: Obtener los colores personalizados del tema actual.
    final customColors = Theme.of(context).extension<CustomColors>()!;

    Color fg; // Foreground color

    if (s.contains('valid') || s.contains('proces')) {
      // ✨ PASO 2: Usar el color de éxito del tema.
      fg = customColors.success!; 
    } else if (s.contains('rechaz') || s.contains('error') || s.contains('fail')) {
      // ✨ PASO 3: Usar el color de error del tema.
      fg = customColors.error!;
    } else {
      // Esta parte ya era correcta, usa el color primario del tema.
      fg = Theme.of(context).colorScheme.primary;
    }
    
    // El resto de tu lógica es perfecta y no necesita cambios.
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
