import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'theme/app_theme.dart';
import 'theme/theme_controller.dart';
import 'screens/splash_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/login_screen.dart';
import 'screens/main_screen.dart'; 
import 'screens/capture_screen.dart';
import 'screens/preview_screen.dart';
import 'screens/document_detail_screen.dart';
import 'screens/profile_screen.dart';
import 'services/documents_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ThemeController.instance.init();

  final prefs = await SharedPreferences.getInstance();
  final bool hasSeenOnboarding = prefs.getBool('hasSeenOnboarding') ?? false;

  runApp(SGIDTApp(hasSeenOnboarding: hasSeenOnboarding));
}

class SGIDTApp extends StatelessWidget {
  final bool hasSeenOnboarding;
  const SGIDTApp({super.key, required this.hasSeenOnboarding});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: ThemeController.instance,
      builder: (_, __) {
        return MaterialApp(
          title: 'SGIDT Móvil',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.light(),
          darkTheme: AppTheme.dark(),
          themeMode: ThemeController.instance.mode,
          
          initialRoute: hasSeenOnboarding ? '/splash' : '/onboarding',

          routes: {
            '/onboarding': (_) => const OnboardingScreen(),
            '/splash': (_) => const SplashScreen(),
            '/login': (_) => const LoginScreen(),
            
            // --- ¡ESTE ES EL CAMBIO CLAVE! ---
            // La ruta /home ahora carga nuestra nueva pantalla contenedora.
            '/home': (_) => const MainScreen(),
            // ------------------------------------

            '/capture': (_) => const CaptureScreen(),
            '/profile': (_) => const ProfileScreen(),
          },
          
          onGenerateRoute: (settings) {
            if (settings.name == '/preview') {
              final path = settings.arguments as String;
              return MaterialPageRoute(
                builder: (_) => PreviewScreen(filePath: path),
              );
            }

            if (settings.name == '/document') {
              final args = settings.arguments;
              Widget screen;

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
                screen = const Scaffold(
                  body: Center(child: Text('Argumento inválido para /document')),
                );
              }
              return MaterialPageRoute(builder: (_) => screen);
            }
            return null;
          },
        );
      },
    );
  }
}

// --- Widget para cargar un documento por su ID (se mantiene igual) ---
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
    _fetchDocument();
  }
  void _fetchDocument() {
    _documentFuture = DocumentsService.fetchDetail(widget.id);
  }
  void _retryFetch() {
    setState(() {
      _fetchDocument();
    });
  }
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, String>>(
      future: _documentFuture,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
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
                      onPressed: _retryFetch,
                      label: const Text('Reintentar'),
                    ),
                  ],
                ),
              ),
            ),
          );
        }
        final doc = snap.data!;
        return DocumentDetailScreen(documento: doc);
      },
    );
  }
}