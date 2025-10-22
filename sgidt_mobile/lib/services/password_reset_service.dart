import 'package:dio/dio.dart';
import 'package:sgidt_mobile/core/api/api_client.dart';
import 'package:sgidt_mobile/core/api/api_exceptions.dart';
import 'package:sgidt_mobile/core/api/api_result.dart';
import 'package:sgidt_mobile/core/api/endpoints.dart';

class PasswordResetService {
  // Usamos el ApiClient que ya tienes configurado.
  // Es perfecto porque solo añade el token si existe, por lo que funciona
  // para estas llamadas públicas.
  final Dio _dio = ApiClient.instance.dio;

  /// Paso 1: Solicita un código de reseteo al backend.
  Future<Result<void>> requestPasswordReset(String email) async {
    try {
      await _dio.post(
        Endpoints.passwordRequest,
        data: {'email': email},
      );
      // Si la llamada es exitosa (código 200), devolvemos Success.
      // 'void' se representa como 'null'.
      return const Success(null); 
    } on DioException catch (e) {
      // Tu interceptor de errores ya convierte los errores de Dio a ApiExceptions.
      final error = e.error is ApiException ? e.error as ApiException : ApiException(e.message ?? 'Error desconocido');
      return Failure(error);
    }
  }

  /// Paso 2: Verifica si el código de 6 dígitos es válido.
  Future<Result<void>> verifyPasswordResetCode(String email, String code) async {
    try {
      await _dio.post(
        Endpoints.passwordVerify,
        data: {'email': email, 'code': code},
      );
      return const Success(null);
    } on DioException catch (e) {
      final error = e.error is ApiException ? e.error as ApiException : ApiException('El código es inválido o ha expirado.');
      return Failure(error);
    }
  }

  /// Paso 3: Establece la nueva contraseña.
  Future<Result<void>> setNewPassword({
    required String email,
    required String code,
    required String newPassword,
  }) async {
    try {
      await _dio.post(
        Endpoints.passwordSet,
        data: {
          'email': email,
          'code': code,
          'password': newPassword,
        },
      );
      return const Success(null);
    } on DioException catch (e) {
      final error = e.error is ApiException ? e.error as ApiException : ApiException('No se pudo actualizar la contraseña.');
      return Failure(error);
    }
  }
}