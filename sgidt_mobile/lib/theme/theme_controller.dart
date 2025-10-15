import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeController extends ChangeNotifier {
  ThemeController._();
  static final ThemeController instance = ThemeController._();

  static const _kKey = 'theme_mode'; // 'light' | 'dark' | 'system'

  ThemeMode _mode = ThemeMode.system;
  ThemeMode get mode => _mode;

  bool get isDark =>
      _mode == ThemeMode.dark ||
      (_mode == ThemeMode.system &&
          WidgetsBinding.instance.platformDispatcher.platformBrightness ==
              Brightness.dark);

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
      default:
        _mode = ThemeMode.system;
    }
    notifyListeners();
  }

  Future<void> setMode(ThemeMode m) async {
    _mode = m;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _kKey,
      m == ThemeMode.light ? 'light' : m == ThemeMode.dark ? 'dark' : 'system',
    );
  }

  // This method wasn't quite a toggle, it was more of a setter.
  // We'll leave it in case you use it elsewhere.
  Future<void> toggleDark(bool value) async {
    await setMode(value ? ThemeMode.dark : ThemeMode.light);
  }

  // ✨ --- NEW METHOD --- ✨
  /// Toggles the theme between light and dark mode.
  Future<void> toggleTheme() async {
    // If it's currently dark (or system dark), switch to light. Otherwise, switch to dark.
    final newMode = isDark ? ThemeMode.light : ThemeMode.dark;
    await setMode(newMode);
  }
}