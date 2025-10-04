import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});
  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();
  int _index = 0;

  final List<_SlideData> _slides = const [
    _SlideData(
      title: 'Bienvenido a SGIDT',
      text: 'Captura documentos con tu teléfono.\nRápido y sencillo.',
    ),
    _SlideData(
      title: 'Súbelos a SGIDT',
      text: 'Sincroniza automáticamente con tu empresa\npara mantener todo ordenado.',
    ),
    _SlideData(
      title: 'Validación automática',
      text: '¡Comencemos!',
    ),
  ];

  void _goNext() {
    if (_index < _slides.length - 1) {
      _controller.nextPage(
        duration: const Duration(milliseconds: 280),
        curve: Curves.easeOut,
      );
    } else {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  void _skip() => Navigator.pushReplacementNamed(context, '/login');

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          PageView.builder(
            controller: _controller,
            itemCount: _slides.length,
            onPageChanged: (i) => setState(() => _index = i),
            itemBuilder: (_, i) => _OnboardingSlide(
              slide: _slides[i],
              isLast: i == _slides.length - 1,
            ),
          ),

          // Skip chip (arriba derecha)
          SafeArea(
            child: Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.only(right: 16, top: 10),
                child: _SkipChip(onTap: _skip),
              ),
            ),
          ),

          // Indicadores + flecha (abajo)
          SafeArea(
            child: Align(
              alignment: Alignment.bottomCenter,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 22),
                child: Row(
                  children: [
                    _PagerIndicator(length: _slides.length, index: _index),
                    const Spacer(),
                    _RoundGhostButton(
                      onTap: _goNext,
                      child: const Icon(Icons.arrow_forward, color: Colors.white),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/* ---------------------------------------------
 *   Slide visual con blob + textos
 * --------------------------------------------- */
class _OnboardingSlide extends StatelessWidget {
  const _OnboardingSlide({required this.slide, required this.isLast});
  final _SlideData slide;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    const purpleDeep = Color(0xFF2A1140);
    const purple = Color(0xFF4A1D6A);
    const magenta = Color(0xFFD63C7B);
    const yellow = Color(0xFFF7D700);

    return LayoutBuilder(
      builder: (_, constraints) {
        return Stack(
          children: [
            // Fondo degradado
            Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [purpleDeep, purple],
                  begin: Alignment(-0.8, -1.0),
                  end: Alignment(0.8, 1.0),
                ),
              ),
            ),

            // Círculos decorativos sutiles
            Positioned(
              left: -40,
              top: 60,
              child: Container(
                width: 90,
                height: 90,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(.06),
                  shape: BoxShape.circle,
                ),
              ),
            ),
            Positioned(
              right: -24,
              top: -14,
              child: Container(
                width: 118,
                height: 118,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(.06),
                  shape: BoxShape.circle,
                ),
              ),
            ),

            // Blob inferior
            Align(
              alignment: Alignment.bottomCenter,
              child: ClipPath(
                clipper: _BlobClipper(),
                child: Container(
                  height: constraints.maxHeight * 0.42,
                  color: magenta,
                ),
              ),
            ),

            // Contenido textual
            Positioned(
              left: 24,
              right: 24,
              bottom: 96,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isLast ? '' : slide.title.toUpperCase(),
                    style: TextStyle(
                      color: isLast ? Colors.white : yellow,
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                      letterSpacing: .5,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    slide.text,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: isLast ? 20 : 15,
                      fontWeight: isLast ? FontWeight.w700 : FontWeight.normal,
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}

/* ---------------------------------------------
 *   Widgets reutilizables
 * --------------------------------------------- */

class _RoundGhostButton extends StatelessWidget {
  final VoidCallback onTap;
  final Widget child;
  const _RoundGhostButton({required this.onTap, required this.child});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(.14),
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: Colors.white24),
        ),
        child: Center(child: child),
      ),
    );
  }
}

class _SkipChip extends StatelessWidget {
  final VoidCallback onTap;
  const _SkipChip({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(.12),
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: Colors.white24),
        ),
        child: const Text(
          'Skip',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}

class _PagerIndicator extends StatelessWidget {
  const _PagerIndicator({required this.length, required this.index});
  final int length;
  final int index;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(length, (i) {
        final active = i == index;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          margin: const EdgeInsets.symmetric(horizontal: 4),
          height: 10,
          width: active ? 32 : 10,
          decoration: BoxDecoration(
            color: active ? AppTheme.sgidtRed : Colors.white.withOpacity(.4),
            borderRadius: BorderRadius.circular(999),
          ),
        );
      }),
    );
  }
}

/* ---------------------------------------------
 *   Utilidades / modelos
 * --------------------------------------------- */

class _SlideData {
  final String title;
  final String text;
  const _SlideData({required this.title, required this.text});
}

/// ClipPath para blob orgánico inferior
class _BlobClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    final p = Path();
    p.moveTo(0, size.height * 0.38);
    p.quadraticBezierTo(size.width * 0.00, size.height * 0.08, size.width * 0.26, 0);
    p.lineTo(size.width * 0.95, 0);
    p.quadraticBezierTo(size.width, 0, size.width, size.height * 0.12);
    p.lineTo(size.width, size.height);
    p.lineTo(0, size.height);
    p.close();
    return p;
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}
