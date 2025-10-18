import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:intl/intl.dart';
// <-- 1. IMPORTAR EL PAQUETE DE LOCALIZACIONES -->
import 'package:flutter_localizations/flutter_localizations.dart'; 

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
  // Asegura que Flutter esté listo
  WidgetsFlutterBinding.ensureInitialized();

  // Inicializa el formato de fechas para español
  Intl.defaultLocale = 'es';
  await initializeDateFormatting('es', null);

  // Inicializa el controlador de tema
  await ThemeController.instance.init();

  // Verifica si el onboarding ya se ha visto
  final prefs = await SharedPreferences.getInstance();
  final bool hasSeenOnboarding = prefs.getBool('hasSeenOnboarding') ?? false;

  // Lanza la aplicación
  runApp(SGIDTApp(hasSeenOnboarding: hasSeenOnboarding));
}

class SGIDTApp extends StatelessWidget {
  final bool hasSeenOnboarding;
  const SGIDTApp({super.key, required this.hasSeenOnboarding});

  @override
  Widget build(BuildContext context) {
    // Obtiene los temas base definidos en app_theme.dart
    final lightThemeBase = AppTheme.light();
    final darkThemeBase = AppTheme.dark();

    // Construye la aplicación usando AnimatedBuilder para reaccionar a cambios de tema
    return AnimatedBuilder(
      animation: ThemeController.instance,
      builder: (_, __) {
        return MaterialApp(
          title: 'SGIDT Móvil',
          debugShowCheckedModeBanner: false, // Oculta la cinta de debug

          // Aplica la tipografía RobotoCondensed a los temas claro y oscuro
          theme: lightThemeBase.copyWith(
            textTheme: GoogleFonts.robotoCondensedTextTheme(lightThemeBase.textTheme),
          ),
          darkTheme: darkThemeBase.copyWith(
            textTheme: GoogleFonts.robotoCondensedTextTheme(darkThemeBase.textTheme),
          ),

          // Usa el modo de tema (claro/oscuro/sistema) del controlador
          themeMode: ThemeController.instance.mode,

          // --- 2. AÑADE ESTOS PARÁMETROS PARA EL CALENDARIO ---
          locale: const Locale('es'), // Define español como el idioma por defecto
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: const [
            Locale('es'), // Tu idioma principal
            Locale('en'), // Un idioma de respaldo (buena práctica)
          ],
          // --- FIN DE LAS LÍNEAS AÑADIDAS ---

          // Define la ruta inicial basada en si se vio el onboarding
          initialRoute: hasSeenOnboarding ? '/splash' : '/onboarding',

          // Define las rutas nombradas de la aplicación
          routes: {
            '/onboarding': (_) => const OnboardingScreen(),
            '/splash': (_) => const SplashScreen(),
            '/login': (_) => const LoginScreen(),
            '/home': (_) => const MainScreen(), // La ruta principal ahora es MainScreen
            '/capture': (_) => const CaptureScreen(),
            '/profile': (_) => const ProfileScreen(),
            // Las rutas '/preview' y '/document' se manejan con onGenerateRoute
          },

          // Maneja rutas generadas dinámicamente (con argumentos)
          onGenerateRoute: (settings) {
            // Ruta para la previsualización de imagen
            if (settings.name == '/preview') {
              final path = settings.arguments as String;
              return MaterialPageRoute(
                builder: (_) => PreviewScreen(filePath: path),
              );
            }

            // Ruta para ver el detalle de un documento
            if (settings.name == '/document') {
              final args = settings.arguments;
              Widget screen;

              // Si los argumentos son un Map<String, String>, usa DocumentDetailScreen directamente
              if (args is Map<String, String>) {
                screen = DocumentDetailScreen(documento: args);
              }
              // Si es otro tipo de Map, intenta convertirlo
              else if (args is Map) {
                final strMap = args.map<String, String>(
                  (k, v) => MapEntry(k.toString(), v?.toString() ?? ''),
                );
                screen = DocumentDetailScreen(documento: strMap);
              }
              // Si el argumento es un ID (String o int), usa DocumentDetailByIdScreen
              else if (args is String || args is int) {
                screen = DocumentDetailByIdScreen(id: args.toString());
              }
              // Si los argumentos no son válidos, muestra un error
              else {
                screen = const Scaffold(
                  body: Center(child: Text('Argumento inválido para /document')),
                );
              }
              return MaterialPageRoute(builder: (_) => screen);
            }
            // Si la ruta no coincide con ninguna, devuelve null
            return null;
          },
        );
      },
    );
  }
}

// --- Widget para cargar detalles de un documento por su ID ---
// (Este widget se usa cuando navegas a /document con un ID como argumento)
class DocumentDetailByIdScreen extends StatefulWidget {
  final String id;
  const DocumentDetailByIdScreen({super.key, required this.id});
  @override
  State<DocumentDetailByIdScreen> createState() => _DocumentDetailByIdScreenState();
}

class _DocumentDetailByIdScreenState extends State<DocumentDetailByIdScreen> {
  // Future para almacenar el resultado de la llamada a la API
  late Future<Map<String, String>> _documentFuture;

  @override
  void initState() {
    super.initState();
    // Llama a la API cuando el widget se inicializa
    _fetchDocument();
  }

  // Función para obtener los detalles del documento
  void _fetchDocument() {
    // Usa el método estático del servicio (o la instancia si la tienes)
    _documentFuture = DocumentsService.fetchDetail(widget.id);
  }

  // Función para reintentar la carga si falla
  void _retryFetch() {
    setState(() {
      _fetchDocument(); // Vuelve a llamar a la API
    });
  }

  @override
  Widget build(BuildContext context) {
    // FutureBuilder maneja los estados de carga, error y éxito
    return FutureBuilder<Map<String, String>>(
      future: _documentFuture,
      builder: (context, snap) {
        // Muestra un indicador de carga mientras espera
        if (snap.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        // Muestra un mensaje de error si la carga falla
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
                      '${snap.error}', // Muestra el mensaje de error específico
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
        // Si la carga fue exitosa, muestra la pantalla de detalles con los datos
        final doc = snap.data!;
        return DocumentDetailScreen(documento: doc);
      },
    );
  }
}