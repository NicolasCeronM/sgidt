class AuthService {
  static String? _token;

  static Future<bool> login(String user, String pass) async {
    await Future.delayed(const Duration(milliseconds: 600));
    // TODO: pegar a tu API Django (token JWT)
    _token = 'token_mock';
    return true;
  }

  static String? get token => _token;

  static void logout() {
    _token = null;
  }
}
