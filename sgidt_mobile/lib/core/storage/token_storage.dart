import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class TokenStorage {
  static const _kAccess   = 'jwt_access';
  static const _kRefresh  = 'jwt_refresh';
  static const _kUser     = 'user_json';
  static const _kEmpresas = 'empresas_json';
  static const _kEmpresaSelId = 'empresa_sel_id';

  // ===== Tokens =====
  static Future<void> saveTokens({required String access, String? refresh}) async {
    final sp = await SharedPreferences.getInstance();
    await sp.setString(_kAccess, access);
    if (refresh != null) await sp.setString(_kRefresh, refresh);
  }

  static Future<String?> get access async {
    final sp = await SharedPreferences.getInstance();
    return sp.getString(_kAccess);
  }

  static Future<String?> get refresh async {
    final sp = await SharedPreferences.getInstance();
    return sp.getString(_kRefresh);
  }

  static Future<bool> isLoggedIn() async => (await access)?.isNotEmpty == true;

  // ===== User/Empresas =====
  static Future<void> saveUser(Map<String, dynamic> user) async {
    final sp = await SharedPreferences.getInstance();
    await sp.setString(_kUser, jsonEncode(user));
  }

  static Future<Map<String, dynamic>?> getUser() async {
    final sp = await SharedPreferences.getInstance();
    final raw = sp.getString(_kUser);
    if (raw == null) return null;
    return jsonDecode(raw) as Map<String, dynamic>;
  }

  static Future<void> saveEmpresas(List empresas) async {
    final sp = await SharedPreferences.getInstance();
    await sp.setString(_kEmpresas, jsonEncode(empresas));
  }

  static Future<List<Map<String, dynamic>>> getEmpresas() async {
    final sp = await SharedPreferences.getInstance();
    final raw = sp.getString(_kEmpresas);
    if (raw == null) return <Map<String, dynamic>>[];
    final list = jsonDecode(raw) as List;
    return list.cast<Map<String, dynamic>>();
  }

  // Empresa seleccionada (opcional)
  static Future<void> setEmpresaSeleccionada(int empresaId) async {
    final sp = await SharedPreferences.getInstance();
    await sp.setInt(_kEmpresaSelId, empresaId);
  }

  static Future<int?> getEmpresaSeleccionada() async {
    final sp = await SharedPreferences.getInstance();
    return sp.getInt(_kEmpresaSelId);
  }

  // ===== Clear all =====
  static Future<void> clear() async {
    final sp = await SharedPreferences.getInstance();
    await sp.remove(_kAccess);
    await sp.remove(_kRefresh);
    await sp.remove(_kUser);
    await sp.remove(_kEmpresas);
    await sp.remove(_kEmpresaSelId);
  }
}
