class ApiException implements Exception {
  final int? statusCode;
  final String message;
  ApiException(this.message, {this.statusCode});
  @override
  String toString() => 'ApiException($statusCode): $message';
}

class UnauthorizedException extends ApiException {
  UnauthorizedException([String msg = 'Unauthorized']) : super(msg, statusCode: 401);
}

class NetworkException extends ApiException {
  NetworkException([String msg = 'Network error']) : super(msg);
}

/// ← NUEVO: para compatibilidad con tus screens
class AuthException extends ApiException {
  AuthException(String msg, {int? statusCode}) : super(msg, statusCode: statusCode);
}
