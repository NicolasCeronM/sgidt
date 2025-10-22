import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Barra inferior curva con notch para un FAB central.
/// - index: pestaña activa (0=Inicio, 2=Perfil)
/// - onTap(i): taps en íconos laterales
/// - onCentralTap(): tap del FAB central (Capturar)
class CurvedBottomNav extends StatelessWidget {
  final int index;
  final ValueChanged<int> onTap;
  final VoidCallback onCentralTap;

  const CurvedBottomNav({
    super.key,
    required this.index,
    required this.onTap,
    required this.onCentralTap,
  });

  @override
  Widget build(BuildContext context) {
    final bg = Theme.of(context).colorScheme.surface;
    final inactive = Theme.of(context).colorScheme.onSurface.withOpacity(.7);
    final active = Theme.of(context).colorScheme.onSurface;

    return ClipRRect(
      borderRadius: const BorderRadius.only(
        topLeft: Radius.circular(22),
        topRight: Radius.circular(22),
      ),
      child: BottomAppBar(
        color: bg,
        elevation: 10,
        height: 64,
        shape: const CircularNotchedRectangle(),
        notchMargin: 8,
        padding: EdgeInsets.zero,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _NavIcon(
              icon: Icons.home_outlined,
              isActive: index == 0,
              activeColor: active,
              inactiveColor: inactive,
              onTap: () => onTap(0),
            ),
            const SizedBox(width: 48), // hueco para el FAB
            _NavIcon(
              icon: Icons.person_outline,
              isActive: index == 2,
              activeColor: active,
              inactiveColor: inactive,
              onTap: () => onTap(2),
            ),
          ],
        ),
      ),
    );
  }
}

class _NavIcon extends StatelessWidget {
  final IconData icon;
  final bool isActive;
  final Color activeColor, inactiveColor;
  final VoidCallback onTap;

  const _NavIcon({
    required this.icon,
    required this.isActive,
    required this.activeColor,
    required this.inactiveColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkResponse(
      onTap: onTap,
      radius: 28,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isActive ? AppTheme.sgidtRed.withOpacity(.10) : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Icon(icon, color: isActive ? activeColor : inactiveColor),
      ),
    );
  }
}

/// FAB central (Capturar) que se asienta en el notch
class CaptureFab extends StatelessWidget {
  final VoidCallback onPressed;
  const CaptureFab({super.key, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton(
      onPressed: onPressed,
      backgroundColor: AppTheme.sgidtRed,
      elevation: 6,
      child: const Icon(Icons.document_scanner_outlined, color: Colors.white),
    );
  }
}
