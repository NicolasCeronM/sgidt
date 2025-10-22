import '../core/api/api_client.dart';
import '../core/api/api_result.dart';
import '../core/api/api_exceptions.dart';
import '../core/api/endpoints.dart';



class DocumentsService {
  DocumentsService._();
  static final DocumentsService instance = DocumentsService._();

  // Helpers
  Map<String, String> _stringifyMap(Map data) {
    final out = <String, String>{};
    data.forEach((k, v) => out[k.toString()] = v?.toString() ?? '');
    return out;
  }

  List<Map<String, String>> _stringifyList(List data) {
    return data.map<Map<String, String>>((e) {
      if (e is Map) return _stringifyMap(e);
      return {'value': e?.toString() ?? ''};
    }).toList();
  }

  /// GET /v1/documentos/
  Future<Result<List<Map<String, String>>>> listDocuments({
    int page = 1,
    int pageSize = 10,
    String? docStatus,
    String? search,
    String? ordering = '-created_at',
  }) async {
    try {
      final res = await ApiClient.instance.dio.get(
        Endpoints.documentos,
        queryParameters: {
          'page': page,
          'page_size': pageSize,
          if (docStatus != null) 'docStatus': docStatus,
          if (search != null) 'search': search,
          if (ordering != null) 'ordering': ordering,
        },
      );

      final data = res.data;
      if (data is Map && data['results'] is List) {
        return Success(_stringifyList(data['results']));
      }
      if (data is List) return Success(_stringifyList(data));
      return Failure(ApiException('Formato de respuesta inesperado'));
    } catch (e) {
      return Failure(e is ApiException ? e : ApiException(e.toString()));
    }
  }

  /// GET /v1/documentos/{id}/
  Future<Result<Map<String, String>>> getDocumentDetail(String id) async {
    try {
      final res = await ApiClient.instance.dio.get(Endpoints.documentoDetalle(id));
      if (res.data is Map) {
        return Success(_stringifyMap(res.data as Map));
      }
      return Failure(ApiException('Formato de respuesta inesperado'));
    } catch (e) {
      return Failure(e is ApiException ? e : ApiException(e.toString()));
    }
  }
  // === COMPATIBILIDAD (shims) ===
  static Future<List<Map<String, String>>> fetchRecent() async {
    final r = await DocumentsService.instance.listDocuments(page: 1, pageSize: 10);
    if (r is Success<List<Map<String, String>>>) return r.data;
    final err = (r as Failure).error;
    throw ApiException(err.message, statusCode: err.statusCode);
  }

  static Future<Map<String, String>> fetchDetail(String id) async {
    final r = await DocumentsService.instance.getDocumentDetail(id);
    if (r is Success<Map<String, String>>) return r.data;
    final err = (r as Failure).error;
    throw ApiException(err.message, statusCode: err.statusCode);
  }

  // Alias para compatibilidad con el wrapper usado en la ruta /document
  static Future<Map<String, String>> fetchById(String id) {
  return fetchDetail(id); // reutiliza tu método existente
}

}



