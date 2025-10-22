import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeController extends ChangeNotifier {
  ThemeController._();
  static final ThemeController instance = ThemeController._();

  static const _kKey = 'theme_mode'; // Clave para guardar en SharedPreferences

  ThemeMode _mode = ThemeMode.system;
  ThemeMode get mode => _mode;

  /// Determina si el tema actual efectivo es oscuro.
  /// Esto es verdadero si el modo es explícitamente oscuro, o si es modo sistema
  /// y el sistema operativo está en modo oscuro.
  bool get isDark =>
      _mode == ThemeMode.dark ||
      (_mode == ThemeMode.system &&
          WidgetsBinding.instance.platformDispatcher.platformBrightness ==
              Brightness.dark);

  /// Carga la preferencia de tema guardada al iniciar la app.
  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_kKey);
    switch (raw) {
      case 'light':
        _mode = ThemeMode.light;
        break;
      case 'dark':
        _mode = ThemeMode.dark;
        break;
      default: // Si no hay nada guardado o es 'system'
        _mode = ThemeMode.system;
    }
    notifyListeners();
  }

  /// Establece y guarda un modo de tema específico.
  Future<void> setMode(ThemeMode m) async {
    _mode = m;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    // Guarda el modo como un string simple.
    await prefs.setString(
      _kKey,
      m == ThemeMode.light ? 'light' : m == ThemeMode.dark ? 'dark' : 'system',
    );
  }

  /// ✅ MÉTODO MEJORADO: Rota entre Claro, Oscuro y Automático (Sistema).
  /// Cambia el tema al siguiente modo en el ciclo: Light -> Dark -> System -> Light...
  Future<void> cycleTheme() async {
    final ThemeMode newMode;
    if (mode == ThemeMode.light) {
      newMode = ThemeMode.dark;
    } else if (mode == ThemeMode.dark) {
      newMode = ThemeMode.system;
    } else { // El modo actual es ThemeMode.system
      newMode = ThemeMode.light;
    }
    await setMode(newMode);
  }

  // El método original `toggleTheme` se puede eliminar o dejar si se usa en otro lugar.
  // Para este caso, lo comentaremos para evitar confusiones.
  /*
  Future<void> toggleTheme() async {
    final newMode = isDark ? ThemeMode.light : ThemeMode.dark;
    await setMode(newMode);
  }
  */
}