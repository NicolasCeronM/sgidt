import 'dart:convert';
import 'package:http/http.dart' as http;
import '../services/auth_service.dart';

class DocumentsService {
  // 🔧 Ajusta a tu backend real
  static const String kApiBaseUrl = 'http://localhost:8000/api';
  static const String kDocumentsEndpoint = '/v1/documentos/'; // listado/creación
  static String kDocumentDetail(String id) => '/documentos/$id/';

  static Uri _url(String path) => Uri.parse('$kApiBaseUrl$path');

  // ---- Helpers de tipado ----
  static Map<String, String> _stringifyMap(Map data) {
    final out = <String, String>{};
    data.forEach((k, v) {
      out[k.toString()] = v?.toString() ?? '';
    });
    return out;
  }

  static List<Map<String, String>> _stringifyList(dynamic data) {
    // data puede ser List o Map con 'results'
    if (data is List) {
      return data
          .where((e) => e is Map)
          .map<Map<String, String>>((e) => _stringifyMap(e as Map))
          .toList();
    }
    if (data is Map && data['results'] is List) {
      return (data['results'] as List)
          .where((e) => e is Map)
          .map<Map<String, String>>((e) => _stringifyMap(e as Map))
          .toList();
    }
    return <Map<String, String>>[];
  }

  // ---- API base (interno) ----
  static Future<dynamic> _getJson(Uri uri) async {
    final headers = {
      'Content-Type': 'application/json',
      ...await AuthService.authHeader(),
    };
    final res = await http.get(uri, headers: headers);

    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body);
    }
    throw Exception('Error ${res.statusCode}: ${res.body}');
  }

  // ==== Usadas por tu código nuevo (si las necesitas) ====
  static Future<Map<String, dynamic>> listDocumentsRaw({int page = 1, int pageSize = 20}) async {
    final uri = Uri.parse('$kApiBaseUrl$kDocumentsEndpoint?page=$page&page_size=$pageSize');
    final data = await _getJson(uri);
    if (data is Map<String, dynamic>) return data;
    if (data is List) {
      return {
        'results': data,
        'count': data.length,
        'next': null,
        'previous': null,
      };
    }
    return {'results': [], 'count': 0, 'next': null, 'previous': null};
  }

  static Future<Map<String, dynamic>> getDocumentDetailRaw(String id) async {
    final data = await _getJson(_url(kDocumentDetail(id)));
    if (data is Map<String, dynamic>) return data;
    if (data is Map) return Map<String, dynamic>.from(data);
    throw Exception('Formato inesperado en detalle');
  }

  // ==== ALIAS COMPATIBLES (para tus pantallas actuales) ====

  /// HomeScreen espera `DocumentsService.fetchRecent()` -> List<Map<String, String>>
  static Future<List<Map<String, String>>> fetchRecent({int page = 1, int pageSize = 20}) async {
    final uri = Uri.parse('$kApiBaseUrl$kDocumentsEndpoint?page=$page&page_size=$pageSize');
    final data = await _getJson(uri);
    return _stringifyList(data);
  }

  /// DocumentDetailScreen espera `DocumentsService.fetchDetail(id)` -> Map<String, String>
  static Future<Map<String, String>> fetchDetail(String id) async {
    final data = await _getJson(_url(kDocumentDetail(id)));
    if (data is Map) {
      return _stringifyMap(data);
    }
    throw Exception('Formato inesperado en detalle');
  }

  // Opcional: eliminar (si lo usas)
  static Future<void> deleteDocument(String id) async {
    final headers = {
      'Content-Type': 'application/json',
      ...await AuthService.authHeader(),
    };
    final res = await http.delete(_url(kDocumentDetail(id)), headers: headers);
    if (res.statusCode >= 200 && res.statusCode < 300) return;
    throw Exception('Error ${res.statusCode}: ${res.body}');
  }
}
