import 'dart:async';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:sgidt_mobile/core/api/endpoints.dart';
import 'package:sgidt_mobile/core/config/app_config.dart';
import 'package:sgidt_mobile/core/storage/token_storage.dart';

class UploadService {
  /// Sube un documento (imagen) al backend.
  ///
  /// Recibe el [filePath] del archivo en el dispositivo.
  /// Devuelve `true` si la subida fue exitosa (código 201), de lo contrario `false`.
  Future<bool> uploadDocument(String filePath) async {
    // 1. Obtener el token de autenticación de forma segura
    final token = await TokenStorage.access;
    if (token == null) {
      print('Error de subida: Usuario no autenticado (token no encontrado).');
      return false;
    }

    // 2. Construir la URL final a partir de la configuración central
    final url = Uri.parse('${AppConfig.apiBaseUrl}${Endpoints.documentos}');
    print('Subiendo a: $url');

    // 3. Crear la solicitud multipart, que es la estándar para archivos
    var request = http.MultipartRequest('POST', url);

    // 4. Adjuntar el token de autorización en los headers
    request.headers['Authorization'] = 'Bearer $token';

    // 5. Adjuntar el archivo
    try {
      // 'archivo' es el nombre del campo que Django espera.
      // ¡Asegúrate de que coincida con el nombre en tu `DocumentoSerializer`!
      request.files.add(await http.MultipartFile.fromPath('files', filePath));
    } catch (e) {
      print('Error crítico al leer el archivo: $e');
      return false;
    }

    // 6. Enviar la solicitud y manejar la respuesta
    try {
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 201) {
        print('✅ Documento subido con éxito. Respuesta: ${response.body}');
        return true;
      } else {
        print('❌ Error del servidor. Código: ${response.statusCode}. Respuesta: ${response.body}');
        return false;
      }
    } catch (e) {
      print('❌ Excepción de red durante la subida: $e');
      return false;
    }
  }
}