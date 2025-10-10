import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../services/auth_service.dart';

class UploadService {
  static const String kApiBaseUrl = 'http://localhost:8000/api'; // o por dart-define
  static const String kUploadEndpoint = '/v1/documentos/';

  static Uri _url(String path) => Uri.parse('$kApiBaseUrl$path');

  static Future<Map<String, dynamic>> uploadFile({
    required File file,
    String fileFieldName = 'file',
    Map<String, String>? extraFields,
  }) async {
    final uri = _url(kUploadEndpoint);
    final req = http.MultipartRequest('POST', uri);

    final Map<String, String> headers = <String, String>{};
    final auth = await AuthService.authHeader();
    if (auth.isNotEmpty) headers.addAll(auth);
    req.headers.addAll(headers);

    if (extraFields != null) req.fields.addAll(extraFields);
    final fileName = file.path.split(Platform.pathSeparator).last;
    req.files.add(await http.MultipartFile.fromPath(fileFieldName, file.path, filename: fileName));

    final streamed = await req.send();
    final res = await http.Response.fromStream(streamed);

    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    try {
      final err = jsonDecode(res.body);
      final detail = (err is Map && err['detail'] != null) ? err['detail'].toString() : res.body;
      throw Exception(detail);
    } catch (_) {
      throw Exception('Error ${res.statusCode}: ${res.body}');
    }
  }

  static Future<bool> uploadImage(File file) async {
    try { await uploadFile(file: file, fileFieldName: 'file'); return true; }
    catch (_) { return false; }
  }
}
