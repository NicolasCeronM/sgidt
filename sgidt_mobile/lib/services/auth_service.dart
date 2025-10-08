import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AuthService {
  AuthService._();
  static final AuthService instance = AuthService._();

  /// Base de API (inyectable con --dart-define)
  /// En dev móvil físico usa:
  ///   - ADB reverse:  http://localhost:8000/api
  ///   - IP del PC:    http://192.168.x.x:8000/api
  static const String _base = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api',
  );

  static Uri _u(String path) => Uri.parse('$_base$path');

  // ---------------- Token storage ----------------

  static const _kToken = 'auth_token';
  static const _kIsBearer = 'auth_is_bearer';

  static Future<void> _saveToken(String token, {required bool bearer}) async {
    final sp = await SharedPreferences.getInstance();
    await sp.setString(_kToken, token);
    await sp.setBool(_kIsBearer, bearer);
  }

  static Future<void> logout() async {
    final sp = await SharedPreferences.getInstance();
    await sp.remove(_kToken);
    await sp.remove(_kIsBearer);
  }

  static Future<bool> isLoggedIn() async {
    final sp = await SharedPreferences.getInstance();
    return (sp.getString(_kToken) ?? '').isNotEmpty;
  }

  static Future<Map<String, String>> authHeader() async {
    final sp = await SharedPreferences.getInstance();
    final token = sp.getString(_kToken);
    if (token == null || token.isEmpty) return {};
    final isBearer = sp.getBool(_kIsBearer) ?? true;
    return {'Authorization': isBearer ? 'Bearer $token' : 'Token $token'};
  }

  // ------------------- LOGIN ---------------------

  /// Hace POST a /api/auth/login/ (o el que tengas configurado)
  /// Guarda el token automáticamente. Lanza [AuthException] con
  /// mensajes legibles si falla.
  static Future<void> login(String userOrEmail, String password) async {
    final client = http.Client();
    try {
      final headers = {'Content-Type': 'application/json'};

      // 1) Intento con "username"
      var res = await client
          .post(_u('/auth/login/'),
              headers: headers,
              body: jsonEncode({'username': userOrEmail, 'password': password}))
          .timeout(const Duration(seconds: 20));

      // 2) Si falló, intento con "email" (algunos endpoints lo requieren)
      if (res.statusCode >= 400) {
        res = await client
            .post(_u('/auth/login/'),
                headers: headers,
                body:
                    jsonEncode({'email': userOrEmail, 'password': password}))
            .timeout(const Duration(seconds: 20));
      }

      if (res.statusCode < 200 || res.statusCode >= 300) {
        // Intenta extraer "detail" de DRF
        String msg;
        try {
          final body = jsonDecode(res.body);
          msg = body['detail']?.toString() ??
              body['message']?.toString() ??
              'Credenciales inválidas';
        } catch (_) {
          msg = 'Error ${res.statusCode} en login';
        }
        throw AuthException(msg, statusCode: res.statusCode);
      }

      final body = jsonDecode(res.body);

      // Soporta formatos comunes
      final token =
          body['access'] ?? body['token'] ?? body['key'] ?? body['auth_token'];
      if (token == null || token.toString().isEmpty) {
        throw const AuthException('La respuesta no contiene token.');
      }

      // Si viene "access" asumimos Bearer (JWT), si no, Token
      final isBearer = body.containsKey('access');
      await _saveToken(token.toString(), bearer: isBearer);
    } on SocketException {
      throw const AuthException(
          'No se pudo conectar con el servidor. ¿Está arriba en 8000?');
    } on TimeoutException {
      throw const AuthException('Tiempo de espera agotado. Intenta de nuevo.');
    } on AuthException {
      rethrow;
    } catch (e) {
      throw AuthException('Error inesperado: $e');
    } finally {
      client.close();
    }
  }
}

class AuthException implements Exception {
  final String message;
  final int? statusCode;
  const AuthException(this.message, {this.statusCode});
  @override
  String toString() => 'AuthException($statusCode): $message';
}
