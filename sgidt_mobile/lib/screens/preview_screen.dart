import 'dart:io';
import 'package:flutter/material.dart';
import 'package:sgidt_mobile/services/upload_service.dart';

class PreviewScreen extends StatefulWidget {
  final String filePath;
  const PreviewScreen({super.key, required this.filePath});

  @override
  State<PreviewScreen> createState() => _PreviewScreenState();
}

class _PreviewScreenState extends State<PreviewScreen> {
  final UploadService _uploadService = UploadService();
  bool _isUploading = false;

  Future<void> _handleUpload() async {
    if (_isUploading) return; // Prevenir múltiples clics

    setState(() {
      _isUploading = true;
    });

    final success = await _uploadService.uploadDocument(widget.filePath);

    // Verificar que el widget todavía existe antes de actualizar la UI
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success
              ? '✅ ¡Documento enviado con éxito!'
              : '❌ Error al enviar el documento. Inténtalo de nuevo.'),
          backgroundColor: success ? Colors.green.shade700 : Colors.red.shade700,
        ),
      );

      if (success) {
        // Si la subida fue exitosa, volvemos a la pantalla de inicio
        Navigator.of(context).popUntil((route) => route.isFirst);
      } else {
        // Si falló, solo detenemos la carga para que pueda reintentar
        setState(() {
          _isUploading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Confirmar y Enviar'),
        elevation: 1,
      ),
      body: Column(
        children: [
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(8.0),
              child: Image.file(File(widget.filePath), fit: BoxFit.contain),
            ),
          ),
          // Mostramos un indicador de progreso lineal y claro
          if (_isUploading)
            const Padding(
              padding: EdgeInsets.all(16.0),
              child: Column(
                children: [
                  LinearProgressIndicator(),
                  SizedBox(height: 8),
                  Text('Enviando documento...', style: TextStyle(fontSize: 16)),
                ],
              ),
            ),
          // El botón principal para la acción de subir
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            child: FilledButton.icon(
              // Deshabilitamos el botón mientras se sube el archivo
              onPressed: _isUploading ? null : _handleUpload,
              icon: const Icon(Icons.cloud_upload_outlined),
              label: const Text('Subir a SGIDT'),
              style: FilledButton.styleFrom(
                minimumSize: const Size(double.infinity, 50),
                textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      ),
    );
  }
}