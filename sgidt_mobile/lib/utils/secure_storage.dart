import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  static const _kAccess = 'access_token';
  static const _kRefresh = 'refresh_token';

  static const FlutterSecureStorage _storage = FlutterSecureStorage();

  static Future<void> saveTokens({required String access, String? refresh}) async {
    await _storage.write(key: _kAccess, value: access);
    if (refresh != null) {
      await _storage.write(key: _kRefresh, value: refresh);
    }
  }

  static Future<String?> getAccess() => _storage.read(key: _kAccess);
  static Future<String?> getRefresh() => _storage.read(key: _kRefresh);

  static Future<void> clear() async {
    await _storage.delete(key: _kAccess);
    await _storage.delete(key: _kRefresh);
  }
}
