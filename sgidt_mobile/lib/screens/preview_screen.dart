import 'dart:io';
import 'package:flutter/material.dart';
import '../services/upload_service.dart';

class PreviewScreen extends StatefulWidget {
  final String filePath;
  const PreviewScreen({super.key, required this.filePath});

  @override
  State<PreviewScreen> createState() => _PreviewScreenState();
}

class _PreviewScreenState extends State<PreviewScreen> {
  bool _uploading = false;
  String? _result;

  Future<void> _upload() async {
    setState(() { _uploading = true; _result = null; });
    final ok = await UploadService.uploadImage(File(widget.filePath));
    setState(() {
      _uploading = false;
      _result = ok ? 'Subido correctamente' : 'Error al subir';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Previsualización')),
      body: Column(
        children: [
          Expanded(child: Image.file(File(widget.filePath), fit: BoxFit.contain)),
          if (_uploading) const LinearProgressIndicator(),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                OutlinedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Repetir'),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _uploading ? null : _upload,
                    icon: const Icon(Icons.cloud_upload_outlined),
                    label: const Text('Subir a SGIDT'),
                  ),
                ),
              ],
            ),
          ),
          if (_result != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Text(
                _result!,
                style: TextStyle(
                  color: _result!.startsWith('Error') ? Colors.red : Colors.green,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
