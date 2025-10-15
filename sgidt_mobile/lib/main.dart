import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'theme/theme_controller.dart';
import 'screens/splash_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/capture_screen.dart';
import 'screens/preview_screen.dart';
import 'screens/document_detail_screen.dart';
import 'screens/profile_screen.dart';
import 'services/documents_service.dart';

Future<void> main() async {
  // Asegura que los bindings de Flutter estén inicializados.
  WidgetsFlutterBinding.ensureInitialized();
  // Inicializa el controlador del tema para cargar la preferencia del usuario.
  await ThemeController.instance.init();
  runApp(const SGIDTApp());
}

class SGIDTApp extends StatelessWidget {
  const SGIDTApp({super.key});

  @override
  Widget build(BuildContext context) {
    // AnimatedBuilder reconstruye MaterialApp cuando el tema cambia.
    return AnimatedBuilder(
      animation: ThemeController.instance,
      builder: (_, __) {
        return MaterialApp(
          title: 'SGIDT Móvil',
          debugShowCheckedModeBanner: false,

          // --- Configuración de Tema ---
          theme: AppTheme.light(),
          darkTheme: AppTheme.dark(),
          themeMode: ThemeController.instance.mode,

          // --- Configuración de Rutas ---
          initialRoute: '/splash',
          routes: {
            '/splash': (_) => const SplashScreen(),
            '/onboarding': (_) => const OnboardingScreen(),
            '/login': (_) => const LoginScreen(),
            '/home': (_) => const HomeScreen(),
            '/capture': (_) => const CaptureScreen(),
            '/profile': (_) => const ProfileScreen(),
          },
          
          // ✨ REFACTORIZACIÓN: Lógica de generación de rutas centralizada y más limpia.
          onGenerateRoute: (settings) {
            if (settings.name == '/preview') {
              final path = settings.arguments as String;
              return MaterialPageRoute(
                builder: (_) => PreviewScreen(filePath: path),
              );
            }

            if (settings.name == '/document') {
              final args = settings.arguments;
              Widget screen; // Variable para almacenar la pantalla a mostrar

              if (args is Map<String, String>) {
                screen = DocumentDetailScreen(documento: args);
              } else if (args is Map) {
                final strMap = args.map<String, String>(
                  (k, v) => MapEntry(k.toString(), v?.toString() ?? ''),
                );
                screen = DocumentDetailScreen(documento: strMap);
              } else if (args is String || args is int) {
                screen = DocumentDetailByIdScreen(id: args.toString());
              } else {
                // Pantalla de fallback si los argumentos no son válidos.
                screen = const Scaffold(
                  body: Center(child: Text('Argumento inválido para /document')),
                );
              }
              // Se crea el MaterialPageRoute una sola vez al final.
              return MaterialPageRoute(builder: (_) => screen);
            }

            // Si la ruta no es manejada, retorna null.
            return null;
          },
        );
      },
    );
  }
}

/// ✨ MEJORA: Wrapper convertido a StatefulWidget para permitir reintentar la carga.
/// Obtiene el documento por ID usando un FutureBuilder y luego muestra la pantalla de detalle.
class DocumentDetailByIdScreen extends StatefulWidget {
  final String id;
  const DocumentDetailByIdScreen({super.key, required this.id});

  @override
  State<DocumentDetailByIdScreen> createState() => _DocumentDetailByIdScreenState();
}

class _DocumentDetailByIdScreenState extends State<DocumentDetailByIdScreen> {
  late Future<Map<String, String>> _documentFuture;

  @override
  void initState() {
    super.initState();
    // Inicia la carga del documento cuando el widget se crea por primera vez.
    _fetchDocument();
  }

  void _fetchDocument() {
    _documentFuture = DocumentsService.fetchDetail(widget.id);
  }

  void _retryFetch() {
    // Actualiza el estado para que FutureBuilder se reconstruya y reintente el future.
    setState(() {
      _fetchDocument();
    });
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, String>>(
      future: _documentFuture,
      builder: (context, snap) {
        // --- Estado de Carga ---
        if (snap.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        // --- Estado de Error ---
        if (snap.hasError) {
          return Scaffold(
            appBar: AppBar(title: Text('Documento #${widget.id}')),
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      'Error al cargar el documento.',
                      style: Theme.of(context).textTheme.titleMedium,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${snap.error}',
                      style: Theme.of(context).textTheme.bodySmall,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 24),
                    FilledButton.icon(
                      icon: const Icon(Icons.refresh),
                      onPressed: _retryFetch, // Botón para reintentar
                      label: const Text('Reintentar'),
                    ),
                  ],
                ),
              ),
            ),
          );
        }
        
        // --- Estado Exitoso ---
        final doc = snap.data!;
        return DocumentDetailScreen(documento: doc);
      },
    );
  }
}