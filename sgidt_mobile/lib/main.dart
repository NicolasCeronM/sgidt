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

// Wrapper para cargar detalle por ID
import 'services/documents_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ThemeController.instance.init();
  runApp(const SGIDTApp());
}

class SGIDTApp extends StatelessWidget {
  const SGIDTApp({super.key});

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
          initialRoute: '/splash',
          routes: {
            '/splash': (_) => const SplashScreen(),
            '/onboarding': (_) => const OnboardingScreen(),
            '/login': (_) => const LoginScreen(),
            '/home': (_) => const HomeScreen(),
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

              // Caso 1: ya viene el documento como Map<String, String>
              if (args is Map<String, String>) {
                return MaterialPageRoute(
                  builder: (_) => DocumentDetailScreen(documento: args),
                );
              }

              // Caso 2: viene como Map dinámico -> convertir a <String,String>
              if (args is Map) {
                final strMap = args.map<String, String>(
                  (k, v) => MapEntry(k.toString(), v?.toString() ?? ''),
                );
                return MaterialPageRoute(
                  builder: (_) => DocumentDetailScreen(documento: strMap),
                );
              }

              // Caso 3: solo me pasaron un id -> hago fetch antes de mostrar
              if (args is String || args is int) {
                final id = args.toString();
                return MaterialPageRoute(
                  builder: (_) => DocumentDetailByIdScreen(id: id),
                );
              }

              // Fallback amigable
              return MaterialPageRoute(
                builder: (_) => const Scaffold(
                  body: Center(child: Text('Argumento inválido para /document')),
                ),
              );
            }

            return null;
          },
        );
      },
    );
  }
}

/// Wrapper: obtiene el documento por ID y luego muestra el detalle.
class DocumentDetailByIdScreen extends StatelessWidget {
  final String id;
  const DocumentDetailByIdScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, String>>(
      future: DocumentsService.fetchDetail(id), // Usa tu service existente
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        if (snap.hasError) {
          return Scaffold(
            appBar: AppBar(title: Text('Documento #$id')),
            body: Center(child: Text('Error cargando documento: ${snap.error}')),
          );
        }
        final doc = snap.data!;
        return DocumentDetailScreen(documento: doc);
      },
    );
  }
}
