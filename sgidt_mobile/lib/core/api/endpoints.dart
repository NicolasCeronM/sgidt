class Endpoints {
  // Auth
  static const String login = '/auth/login/';
  static const String refresh = '/auth/refresh/';

  // Documentos
  static const String documentos = '/v1/documentos/';
  static String documentoDetalle(String id) => '/v1/documentos/$id/';
  static const String documentosProgressBatch = '/v1/documentos/progress-batch/';
}
