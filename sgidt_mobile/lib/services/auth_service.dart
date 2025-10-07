import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/secure_storage.dart';

class AuthService {
  static const String kApiBaseUrl = 'http://localhost:8000/api';
  static const String kLoginEndpoint = '/auth/login/'; // o '/token/'
  static const String kMeEndpoint = '/auth/me/';

  static Uri _url(String path) => Uri.parse('$kApiBaseUrl$path');

  static Future<bool> isLoggedIn() async {
    final token = await SecureStorage.getAccess();
    return token != null && token.isNotEmpty;
  }

  static Future<Map<String, String>> authHeader() async {
    final token = await SecureStorage.getAccess();
    if (token == null || token.isEmpty) return {};
    return {'Authorization': 'Bearer $token'};
  }

  static Future<void> login({
    required String usernameOrEmail,
    required String password,
  }) async {
    final body = jsonEncode({
      'username': usernameOrEmail, // cambia a 'email' si tu API lo pide
      'password': password,
    });

    final res = await http.post(
      _url(kLoginEndpoint),
      headers: {'Content-Type': 'application/json'},
      body: body,
    );

    if (res.statusCode == 200 || res.statusCode == 201) {
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final access = (data['access'] ?? data['token'] ?? data['access_token'])?.toString();
      final refresh = (data['refresh'] ?? data['refresh_token'])?.toString();

      if (access == null || access.isEmpty) {
        throw Exception('La respuesta no contiene access token.');
      }
      await SecureStorage.saveTokens(access: access, refresh: refresh);
      return;
    }

    try {
      final err = jsonDecode(res.body);
      final detail = (err is Map && err['detail'] != null) ? err['detail'].toString() : res.body;
      throw Exception(detail);
    } catch (_) {
      throw Exception('Error ${res.statusCode}: ${res.body}');
    }
  }

  static Future<Map<String, dynamic>> me() async {
    final headers = {
      'Content-Type': 'application/json',
      ...await authHeader(),
    };
    final res = await http.get(_url(kMeEndpoint), headers: headers);
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    throw Exception('Error ${res.statusCode}: ${res.body}');
  }

  static Future<void> logout() async {
    await SecureStorage.clear();
  }
}
