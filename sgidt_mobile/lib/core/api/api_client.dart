import 'dart:io';
import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';
import '../config/app_config.dart';
import '../storage/token_storage.dart';
import 'api_exceptions.dart';

class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();

  late final Dio dio = _build();

  Dio _build() {
    final base = AppConfig.apiBaseUrl;
    final d = Dio(BaseOptions(
      baseUrl: base,
      connectTimeout: const Duration(milliseconds: AppConfig.connectTimeoutMs),
      receiveTimeout: const Duration(milliseconds: AppConfig.receiveTimeoutMs),
      headers: {
        HttpHeaders.acceptHeader: 'application/json',
      },
    ));

    // Auth interceptor
    d.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await TokenStorage.access;
        if (token != null && token.isNotEmpty) {
          options.headers[HttpHeaders.authorizationHeader] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (e, handler) {
        // Mapear errores
        if (e.type == DioExceptionType.connectionError ||
            e.type == DioExceptionType.connectionTimeout ||
            e.type == DioExceptionType.receiveTimeout) {
          return handler.reject(DioException(
            requestOptions: e.requestOptions,
            error: NetworkException(),
          ));
        }

        final status = e.response?.statusCode;
        final msg = e.response?.data is Map
            ? (e.response!.data['detail'] ?? e.response!.data['message'] ?? 'Error')
            : (e.message ?? 'Error');

        if (status == 401) {
          return handler.reject(DioException(
            requestOptions: e.requestOptions,
            error: UnauthorizedException(msg.toString()),
          ));
        }

        return handler.reject(DioException(
          requestOptions: e.requestOptions,
          error: ApiException(msg.toString(), statusCode: status),
        ));
      },
    ));

    // Logging sólo en debug
    d.interceptors.add(PrettyDioLogger(
      requestHeader: true,
      requestBody: true,
      responseBody: true,
      responseHeader: false,
      compact: true,
    ));

    return d;
  }
}
