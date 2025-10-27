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
  // ⛔️ Color rojo anterior (ya no se usa como primario)
  // static const Color sgidtRed = Color(0xFFB71C1C);

  // 💡 NUEVO COLOR PRIMARIO RECOMENDADO
  static const Color sgidtBlue = Color(0xFF1565C0); // Colors.blue.shade800

  // ------ LIGHT THEME (MODIFICADO) ------
  static ThemeData light() {
    final baseScheme = ColorScheme.fromSeed(
      // 💡 CAMBIO: Se usa el nuevo azul como 'seed'
      seedColor: sgidtBlue, 
      brightness: Brightness.light,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: baseScheme.copyWith(
        // 💡 CAMBIO: Se define el primario y secundario con el azul
        primary: sgidtBlue,
        secondary: sgidtBlue,
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
        // 💡 CAMBIO: El FAB ahora usa el azul
        backgroundColor: sgidtBlue,
        foregroundColor: Colors.white,
      ),
      extensions: const <ThemeExtension<dynamic>>[
        CustomColors.light,
      ],
    );
  }

  // ------ DARK THEME (Con los cambios a blanco de la petición anterior) ------
  static ThemeData dark() {
    final baseScheme = ColorScheme.fromSeed(
      seedColor: Colors.blueGrey, 
      brightness: Brightness.dark,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: baseScheme.copyWith(
        // Se mantiene en blanco como pediste
        primary: Colors.white,
        secondary: Colors.white,
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
        // Se mantiene en blanco/negro como pediste
        backgroundColor: Colors.white,
        foregroundColor: Colors.black, 
      ),
      extensions: const <ThemeExtension<dynamic>>[
        CustomColors.dark,
      ],
    );
  }
}