import 'dart:io';
import 'package:http/http.dart' as http;
import 'auth_service.dart';

class UploadService {
  // Reemplaza con tu endpoint real en Django:
  static const String _endpoint = 'https://tu-dominio-sgidt/api/upload/';

  static Future<bool> uploadImage(File file) async {
    try {
      final request = http.MultipartRequest('POST', Uri.parse(_endpoint));
      final token = AuthService.token;
      if (token != null) {
        request.headers['Authorization'] = 'Bearer $token';
      }
      request.files.add(await http.MultipartFile.fromPath('file', file.path));
      final response = await request.send();
      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (_) {
      return false;
    }
  }
}
