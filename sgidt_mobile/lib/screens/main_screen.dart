import 'package:flutter/material.dart';
import 'home_screen.dart';       // La pantalla con los 2 botones
import 'profile_screen.dart';     // La pantalla de perfil que ya tienes
// Ya no importamos los widgets de 'documentos_screen.dart'

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _pageIndex = 0; // 0 para Home, 1 para Perfil

  static const List<Widget> _pages = <Widget>[
    HomeScreen(), 
    ProfileScreen(),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _pageIndex = index;
    });
  }

  void _goCapture() {
    Navigator.pushNamed(context, '/capture');
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      body: _pages.elementAt(_pageIndex),

      // Ahora 'CaptureFab' y 'CurvedBottomNav' están definidos abajo en este mismo archivo
      floatingActionButton: CaptureFab(onPressed: _goCapture),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      bottomNavigationBar: CurvedBottomNav(
        index: _pageIndex == 0 ? 0 : 2, 
        onTap: (i) {
          if (i == 0) _onItemTapped(0);
          if (i == 2) _onItemTapped(1);
        },
        onCentralTap: _goCapture,
        bgColor: scheme.surface,
        activeColor: scheme.primary,
      ),
    );
  }
}

// --- WIDGETS DE LA BARRA DE NAVEGACIÓN (AHORA VIVEN AQUÍ) ---

class CurvedBottomNav extends StatelessWidget {
  final int index;
  final ValueChanged<int> onTap;
  final VoidCallback onCentralTap;
  final Color bgColor;
  final Color activeColor;

  const CurvedBottomNav({
    super.key,
    required this.index,
    required this.onTap,
    required this.onCentralTap,
    required this.bgColor,
    required this.activeColor,
  });

  @override
  Widget build(BuildContext context) {
    final inactive = Theme.of(context).colorScheme.onSurface.withOpacity(.6);
    
    return BottomAppBar(
      shape: const CircularNotchedRectangle(),
      notchMargin: 8,
      color: bgColor,
      elevation: 10,
      height: 68,
      padding: EdgeInsets.zero,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _NavIcon(
            icon: Icons.home_outlined,
            isActive: index == 0,
            activeColor: activeColor,
            inactiveColor: inactive,
            onTap: () => onTap(0),
          ),
          const SizedBox(width: 48),
          _NavIcon(
            icon: Icons.person_outline,
            isActive: index == 2,
            activeColor: activeColor,
            inactiveColor: inactive,
            onTap: () => onTap(2),
          ),
        ],
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
          color: isActive ? activeColor.withOpacity(.10) : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Icon(icon, color: isActive ? activeColor : inactiveColor, size: 26),
      ),
    );
  }
}

class CaptureFab extends StatelessWidget {
  final VoidCallback onPressed;
  const CaptureFab({super.key, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 64,
      width: 64,
      child: FloatingActionButton(
        onPressed: onPressed,
        elevation: 6,
        child: const Icon(Icons.document_scanner_outlined, size: 30),
      ),
    );
  }
}