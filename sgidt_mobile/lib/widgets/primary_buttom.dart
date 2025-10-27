import 'package:flutter/material.dart';

class PrimaryButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isLoading; // Nuevo: Para manejar el estado de carga

  const PrimaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
    this.isLoading = false, // Valor por defecto
  });

  @override
  Widget build(BuildContext context) {
    // 1. Estilo estandarizado (tomado del botón de login)
    final style = FilledButton.styleFrom(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    );

    // 2. Contenido del botón: Indicador de carga o ícono/texto
    final Widget buttonContent;
    if (isLoading) {
      // Estado de carga
      buttonContent = const SizedBox(
        width: 24,
        height: 24,
        child: CircularProgressIndicator(strokeWidth: 3, color: Colors.white),
      );
    } else if (icon != null) {
      // Si tiene ícono y no está cargando
      buttonContent = Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      );
    } else {
      // Solo texto
      buttonContent = Text(label, style: const TextStyle(fontWeight: FontWeight.bold));
    }

    // 3. Lógica de onPressed (null si está cargando para deshabilitar)
    final VoidCallback? effectiveOnPressed = isLoading ? null : onPressed;

    // 4. Se envuelve en SizedBox para forzar la altura de 52px
    return SizedBox(
      height: 52,
      child: FilledButton(
        onPressed: effectiveOnPressed,
        style: style,
        child: buttonContent,
      ),
    );
  }
}