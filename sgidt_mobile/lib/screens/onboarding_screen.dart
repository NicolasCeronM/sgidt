import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});
  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();
  int _currentPage = 0;

  // 1. Datos para cada slide, ahora usando IconData en lugar de imágenes.
  final List<_OnboardingSlideData> _slides = const [
    _OnboardingSlideData(
      icon: Icons.document_scanner_outlined,
      title: 'Digitaliza tus documentos',
      description: 'Captura facturas, recibos y cualquier documento importante directamente con la cámara de tu teléfono.',
    ),
    _OnboardingSlideData(
      icon: Icons.cloud_upload_outlined,
      title: 'Organización simplificada',
      description: 'Sube automáticamente tus documentos a la plataforma SGIDT para una gestión eficiente y segura.',
    ),
    _OnboardingSlideData(
      icon: Icons.rocket_launch_outlined,
      title: 'Comienza a transformar tu gestión',
      description: 'Estás listo para experimentar la eficiencia. ¡Vamos a optimizar tu flujo de trabajo!',
    ),
  ];

  Future<void> _onOnboardingComplete() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('hasSeenOnboarding', true);
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/splash');
    }
  }

  void _goToNextPage() {
    if (_currentPage < _slides.length - 1) {
      _controller.nextPage(
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeOutCubic,
      );
    } else {
      _onOnboardingComplete();
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: scheme.surface,
      body: SafeArea(
        child: Column(
          children: [
            // Botón de Saltar
            Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.only(top: 16, right: 16),
                child: TextButton(
                  onPressed: _onOnboardingComplete,
                  child: const Text('Saltar'),
                ),
              ),
            ),
            // Contenido principal con el PageView
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _slides.length,
                onPageChanged: (index) => setState(() => _currentPage = index),
                itemBuilder: (context, index) {
                  return _OnboardingSlide(slide: _slides[index]);
                },
              ),
            ),
            // Controles de navegación inferiores
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _PageIndicator(
                    count: _slides.length,
                    currentIndex: _currentPage,
                    activeColor: scheme.primary,
                    inactiveColor: scheme.onSurface.withOpacity(0.2),
                  ),
                  FloatingActionButton(
                    onPressed: _goToNextPage,
                    elevation: 2,
                    child: Icon(
                      _currentPage == _slides.length - 1 ? Icons.check_rounded : Icons.arrow_forward_rounded,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Clase de datos para cada slide
class _OnboardingSlideData {
  final IconData icon;
  final String title;
  final String description;

  const _OnboardingSlideData({
    required this.icon,
    required this.title,
    required this.description,
  });
}

// Widget para cada slide individual
class _OnboardingSlide extends StatelessWidget {
  final _OnboardingSlideData slide;
  const _OnboardingSlide({required this.slide});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // 2. Contenedor estilizado para el icono
          Container(
            width: 150,
            height: 150,
            decoration: BoxDecoration(
              color: scheme.primaryContainer,
              shape: BoxShape.circle,
            ),
            child: Icon(
              slide.icon,
              size: 72,
              color: scheme.onPrimaryContainer,
            ),
          ),
          const SizedBox(height: 48),
          Text(
            slide.title,
            textAlign: TextAlign.center,
            style: textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold, color: scheme.onSurface),
          ),
          const SizedBox(height: 16),
          Text(
            slide.description,
            textAlign: TextAlign.center,
            style: textTheme.bodyLarge?.copyWith(color: scheme.onSurfaceVariant),
          ),
        ],
      ),
    );
  }
}

// Widget para el indicador de página
class _PageIndicator extends StatelessWidget {
  final int count;
  final int currentIndex;
  final Color activeColor;
  final Color inactiveColor;

  const _PageIndicator({
    required this.count,
    required this.currentIndex,
    required this.activeColor,
    required this.inactiveColor,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(count, (index) {
        return AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
          margin: const EdgeInsets.symmetric(horizontal: 4.0),
          height: 8.0,
          width: currentIndex == index ? 24.0 : 8.0,
          decoration: BoxDecoration(
            color: currentIndex == index ? activeColor : inactiveColor,
            borderRadius: BorderRadius.circular(4.0),
          ),
        );
      }),
    );
  }
}