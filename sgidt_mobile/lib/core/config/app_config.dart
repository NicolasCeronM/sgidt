class AppConfig {
  /// Usa --dart-define=API_BASE_URL=http://192.168.1.100:8000/api
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'localhost:8000/api/v1',
  );

  /// Timeouts (ms)
  static const int connectTimeoutMs = 10000;
  static const int receiveTimeoutMs = 20000;
}
