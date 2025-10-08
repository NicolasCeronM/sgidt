import 'package:flutter/material.dart';

class AppTheme {
  // Colores corporativos
  static const Color sgidtRed = Color(0xFFE2261C);
  static const Color ok       = Color(0xFF16A34A); // verde éxito
  static const Color err      = Color(0xFFDC2626); // rojo error

  // ------ LIGHT ------
  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(
      seedColor: sgidtRed,
      brightness: Brightness.light,
    );

    return ThemeData(
      colorScheme: scheme,
      useMaterial3: true,
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
      ),
      // En tu SDK, ThemeData.cardTheme es CardThemeData
      cardTheme: CardThemeData(
        color: scheme.surface,
        elevation: 0.3,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: sgidtRed,
        foregroundColor: Colors.white,
      ),
    );
  }

  // ------ DARK ------
  static ThemeData dark() {
    final scheme = ColorScheme.fromSeed(
      seedColor: sgidtRed,
      brightness: Brightness.dark,
    );

    return ThemeData(
      colorScheme: scheme,
      useMaterial3: true,
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
      ),
      cardTheme: CardThemeData(
        color: scheme.surface,
        elevation: 0.3,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: sgidtRed,
        foregroundColor: Colors.white,
      ),
    );
  }
}
