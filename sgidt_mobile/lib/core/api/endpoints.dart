class Endpoints {
  // Auth
  static const String login = '/usuarios/auth/login/';
  static const String refresh = '/auth/refresh/';

  // Documentos
  static const String documentos = '/documentos/';
  static String documentoDetalle(String id) => '/documentos/$id/';
  static const String documentosProgressBatch = '/documentos/progress-batch/';
}
