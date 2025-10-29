import 'package:dio/dio.dart';

/// Excepción base para todos los errores de la API.
class ApiException implements Exception {
  final int? statusCode;
  final String message;

  ApiException(this.message, {this.statusCode});

  /// Convierte un error de Dio en una [ApiException] específica.
  factory ApiException.fromDioError(dynamic e) { // <-- ¡AQUÍ ESTÁ LA CORRECCIÓN!
    if (e is DioException) {
      if (e.response != null) {
        // El servidor respondió con un código de error (4xx, 5xx)
        final statusCode = e.response!.statusCode;
        final responseData = e.response!.data;
        String errorMessage = responseData?['detail']?.toString() ?? e.message ?? 'Error del servidor.';

        if (statusCode == 401 || statusCode == 403) {
          return UnauthorizedException(errorMessage);
        }
        return ApiException(errorMessage, statusCode: statusCode);
      } else {
        // Error de conexión, timeout, etc.
        return NetworkException('Error de conexión. Revisa tu red.');
      }
    }
    // Si el error no es de Dio, es un error inesperado.
    return ApiException('Ha ocurrido un error inesperado.');
  }

  @override
  String toString() => 'ApiException($statusCode): $message';
}

/// Excepción para errores de autenticación (401).
class UnauthorizedException extends ApiException {
  UnauthorizedException([String msg = 'No autorizado']) : super(msg, statusCode: 401);
}

/// Excepción para errores de red (sin conexión, timeout).
class NetworkException extends ApiException {
  NetworkException([String msg = 'Error de red']) : super(msg);
}

/// Excepción genérica de autenticación para compatibilidad.
class AuthException extends ApiException {
  AuthException(String msg, {int? statusCode}) : super(msg, statusCode: statusCode);
}