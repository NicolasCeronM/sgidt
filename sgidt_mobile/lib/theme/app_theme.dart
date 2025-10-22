import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// La clase CustomColors se mantiene igual que antes
@immutable
class CustomColors extends ThemeExtension<CustomColors> {
  const CustomColors({
    required this.success,
    required this.error,
  });

  final Color? success;
  final Color? error;

  @override
  CustomColors copyWith({Color? success, Color? error}) {
    return CustomColors(
      success: success ?? this.success,
      error: error ?? this.error,
    );
  }

  @override
  CustomColors lerp(ThemeExtension<CustomColors>? other, double t) {
    if (other is! CustomColors) {
      return this;
    }
    return CustomColors(
      success: Color.lerp(success, other.success, t),
      error: Color.lerp(error, other.error, t),
    );
  }

  static const light = CustomColors(
    success: Color(0xFF16A34A),
    error: Color(0xFFDC2626),
  );

  static const dark = CustomColors(
    success: Color(0xFF4ADE80),
    error: Color(0xFFF87171),
  );
}


class AppTheme {
  static const Color sgidtRed = Color(0xFFE2261C);

  // ------ LIGHT THEME (CON FONDOS NEUTROS) ------
  static ThemeData light() {
    // 1. Usamos una semilla neutra (gris) para obtener fondos blancos/grises puros.
    final baseScheme = ColorScheme.fromSeed(
      seedColor: Colors.grey, // Semilla neutra
      brightness: Brightness.light,
    );

    return ThemeData(
      useMaterial3: true,
      // 2. Sobrescribimos el color primario para mantener la identidad de marca.
      colorScheme: baseScheme.copyWith(
        primary: sgidtRed,
        secondary: sgidtRed,
      ),
      textTheme: GoogleFonts.latoTextTheme(ThemeData(brightness: Brightness.light).textTheme),
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: baseScheme.surface,
        foregroundColor: baseScheme.onSurface,
      ),
      cardTheme: CardThemeData(
        color: baseScheme.surface,
        elevation: 0.3,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: sgidtRed,
        foregroundColor: Colors.white,
      ),
      extensions: const <ThemeExtension<dynamic>>[
        CustomColors.light,
      ],
    );
  }

  // ------ DARK THEME (CON FONDOS NEUTROS) ------
  static ThemeData dark() {
    final baseScheme = ColorScheme.fromSeed(
      seedColor: Colors.blueGrey,
      brightness: Brightness.dark,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: baseScheme.copyWith(
        primary: sgidtRed,
        secondary: sgidtRed,
      ),
      textTheme: GoogleFonts.latoTextTheme(ThemeData(brightness: Brightness.dark).textTheme),
      appBarTheme: AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: baseScheme.surface,
        foregroundColor: baseScheme.onSurface,
      ),
      cardTheme: CardThemeData(
        color: baseScheme.surface,
        elevation: 0.3,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: sgidtRed,
        foregroundColor: Colors.white,
      ),
      extensions: const <ThemeExtension<dynamic>>[
        CustomColors.dark,
      ],
    );
  }
}