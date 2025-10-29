import 'package:dio/dio.dart';
import '../core/api/api_client.dart';
import '../core/api/api_result.dart';
import '../core/api/api_exceptions.dart';
import '../core/api/endpoints.dart';

class ReportesService {
  ReportesService._();
  static final ReportesService instance = ReportesService._();

  /// Obtiene los datos de KPIs y gráficos para un mes y año específicos.
  ///
  /// GET /panel/reportes/kpis/
  Future<Result<Map<String, dynamic>>> getReportData({
    required int year,
    required int month,
  }) async {
    try {
      final res = await ApiClient.instance.dio.get(
        Endpoints.reportes, // Tu endpoint: /panel/reportes/kpis/
        queryParameters: {
          'year': year,
          'month': month,
        },
        // El backend espera esta cabecera para devolver JSON en lugar de HTML
        options: Options(
          headers: {
            'x-requested-with': 'XMLHttpRequest',
          },
        ),
      );

      if (res.data is Map<String, dynamic>) {
        return Success(res.data);
      } else {
        // Si la respuesta no es un mapa, algo salió mal
        return Failure(ApiException('Formato de respuesta inesperado.'));
      }
    } catch (e) {
      // Maneja errores de Dio u otras excepciones
      return Failure(e is ApiException ? e : ApiException.fromDioError(e));
    }
  }
}