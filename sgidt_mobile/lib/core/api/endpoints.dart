class Endpoints {
  // --- AUTH ---
  static const String login = '/usuarios/auth/login/';
  static const String refresh = '/auth/refresh/';

  // --- DOCUEMNTOS ---
  static const String documentos = '/documentos/';
  static String documentoDetalle(String id) => '/documentos/$id/';
  static const String documentosProgressBatch = '/documentos/progress-batch/';

 // --- RESETEO DE CONTRASEÑA ---
  static const String passwordRequest = '/usuarios/password/request/';
  static const String passwordVerify = '/usuarios/password/verify/';
  static const String passwordSet = '/usuarios/password/set/';

  // Reportes
  static const String reportes = '/panel/reportes/kpis/';
}
