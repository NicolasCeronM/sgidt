import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../services/auth_service.dart';

class UploadService {
  // 🔧 Ajusta a tu backend real
  static const String kApiBaseUrl = 'https://tu-backend/api';
  static const String kUploadEndpoint = '/documents/upload/'; // el que tengas

  static Uri _url(String path) => Uri.parse('$kApiBaseUrl$path');

  /// Subida genérica multipart que retorna el JSON de respuesta
  static Future<Map<String, dynamic>> uploadFile({
    required File file,
    String fileFieldName = 'file',
    Map<String, String>? extraFields,
  }) async {
    final headers = {
      ...await AuthService.authHeader(), // no agregues Content-Type aquí
    };

    final request = http.MultipartRequest('POST', _url(kUploadEndpoint));
    request.headers.addAll(headers);

    if (extraFields != null) {
      request.fields.addAll(extraFields);
    }

    final multipartFile = await http.MultipartFile.fromPath(fileFieldName, file.path);
    request.files.add(multipartFile);

    final streamed = await request.send();
    final res = await http.Response.fromStream(streamed);

    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }

    // Error legible
    try {
      final err = jsonDecode(res.body);
      final detail = (err is Map && err['detail'] != null) ? err['detail'].toString() : res.body;
      throw Exception(detail);
    } catch (_) {
      throw Exception('Error ${res.statusCode}: ${res.body}');
    }
  }

  /// === ALIAS COMPATIBLE (para tu PreviewScreen) ===
  /// Devuelve true/false según éxito.
  static Future<bool> uploadImage(File file) async {
    try {
      // Si tu backend espera 'image' en vez de 'file', cambia el nombre del campo
      await uploadFile(file: file, fileFieldName: 'file');
      return true;
    } catch (_) {
      return false;
    }
  }
}
