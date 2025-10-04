import 'screens/splash_screen.dart';
import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/onboarding_screen.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/capture_screen.dart';
import 'screens/preview_screen.dart';
import 'screens/document_detail_screen.dart';
import 'screens/profile_screen.dart';

void main() => runApp(const SGIDTApp());

class SGIDTApp extends StatelessWidget {
  const SGIDTApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SGIDT Móvil',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
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
          return MaterialPageRoute(builder: (_) => PreviewScreen(filePath: path));
        }
        if (settings.name == '/document') {
          final id = settings.arguments as String;
          return MaterialPageRoute(builder: (_) => DocumentDetailScreen(id: id));
        }
        return null;
      },
    );
  }
}
