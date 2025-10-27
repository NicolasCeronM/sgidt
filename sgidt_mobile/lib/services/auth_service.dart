import 'package:dio/dio.dart';

import '../core/api/api_client.dart';
import '../core/api/api_result.dart';
import '../core/api/api_exceptions.dart';
import '../core/api/endpoints.dart';
import '../core/storage/token_storage.dart';

class AuthService {
  AuthService._();
  static final AuthService instance = AuthService._();

  /// Método de instancia que retorna Result — lo usa el shim estático
  Future<Result<Map<String, dynamic>>> loginResult({
    required String username,
    required String password,
  }) async {
    try {
      final res = await ApiClient.instance.dio.post(
        Endpoints.login,
        data: {'username': username, 'password': password},
        options: Options(headers: {'Content-Type': 'application/json'}),
      );

      final data = res.data as Map<String, dynamic>;
      final access   = data['access']?.toString();
      final refresh  = data['refresh']?.toString();
      final user     = (data['user'] ?? {}) as Map<String, dynamic>;
      final empresas = (data['empresas'] ?? []) as List;

      if (access == null || access.isEmpty) {
        return Failure(ApiException('Token de acceso no recibido', statusCode: res.statusCode));
      }

      // Guardar tokens + user + empresas
      await TokenStorage.saveTokens(access: access, refresh: refresh);
      await TokenStorage.saveUser(user);
      await TokenStorage.saveEmpresas(empresas);

      // Seleccionar empresa por defecto (si hay)
      if (empresas.isNotEmpty && empresas.first is Map) {
        final id = (empresas.first as Map)['empresa_id'];
        if (id is int) {
          await TokenStorage.setEmpresaSeleccionada(id);
        }
      }

      return Success(data);
    } on DioException catch (e) {
      final err = e.error is ApiException
          ? e.error as ApiException
          : ApiException(e.message ?? 'Error');
      return Failure(err);
    } catch (e) {
      return Failure(ApiException(e.toString()));
    }
  }

  Future<void> logoutInstance() => TokenStorage.clear();
  Future<bool> isLoggedInInstance() => TokenStorage.isLoggedIn();

  /// Opcional: implementar si usas refresh flow
  Future<Result<String>> refresh() async {
    final r = await TokenStorage.refresh;
    if (r == null || r.isEmpty) return Failure(ApiException('No hay refresh token'));
    try {
      final res = await ApiClient.instance.dio.post(
        Endpoints.refresh,
        data: {'refresh': r},
        options: Options(headers: {'Content-Type': 'application/json'}),
      );
      final access = res.data['access']?.toString();
      if (access == null || access.isEmpty) {
        return Failure(ApiException('Refresh sin access'));
      }
      await TokenStorage.saveTokens(access: access, refresh: r);
      return Success(access);
    } on DioException catch (e) {
      final err = e.error is ApiException
          ? e.error as ApiException
          : ApiException(e.message ?? 'Error');
      return Failure(err);
    } catch (e) {
      return Failure(ApiException(e.toString()));
    }
  }

  // =========================
  // SHIMS DE COMPATIBILIDAD
  // =========================

  /// Antiguo: AuthService.isLoggedIn()
  static Future<bool> isLoggedIn() => AuthService.instance.isLoggedInInstance();

  /// Antiguo: AuthService.logout()
  static Future<void> logout() => AuthService.instance.logoutInstance();

  /// Antiguo: AuthService.login(usuario, pass) que lanza excepción
  static Future<void> login(String username, String password) async {
    final r = await AuthService.instance.loginResult(
      username: username,
      password: password,
    );
    if (r is Success) return;
    
    // Si falla, se obtiene el error original para el código de estado (statusCode).
    final err = (r as Failure).error;
    
    // 💡 MODIFICACIÓN: Usar mensaje estandarizado por seguridad 
    // en lugar de err.message.
    const customErrorMessage = 'Credenciales Incorrectas Reintente';
    
    // Lanza AuthException para que tu LoginScreen lo capture
    throw AuthException(customErrorMessage, statusCode: err.statusCode);
  }

  /// Antiguo: headers para http Multipart/etc.
  static Future<Map<String, String>> authHeader() async {
    final t = await TokenStorage.access;
    return t != null && t.isNotEmpty ? {'Authorization': 'Bearer $t'} : <String, String>{};
  }
}