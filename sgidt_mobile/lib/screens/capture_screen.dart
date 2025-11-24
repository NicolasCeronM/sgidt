import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';

class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key});
  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  final _picker = ImagePicker();
  bool _busy = false;

  Future<void> _takePhoto() async {
    setState(() => _busy = true);
    final photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85, 
      preferredCameraDevice: CameraDevice.rear,
    );
    setState(() => _busy = false);

    if (photo != null && mounted) {
      Navigator.pushNamed(context, '/preview', arguments: photo.path);
    }
  }

  Future<void> _pickDocument() async {
    setState(() => _busy = true);

    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['jpg', 'jpeg', 'png', 'pdf'],
    );

    setState(() => _busy = false);

    if (result != null && result.files.single.path != null && mounted) {
      Navigator.pushNamed(
        context,
        '/preview',
        arguments: result.files.single.path!,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Capturar documento')),
      body: Center(
        child: _busy
            ? const CircularProgressIndicator()
            : Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.document_scanner_outlined, size: 96),
                  const SizedBox(height: 12),
                  const Text('Alinea o sube un documento'),
                  const SizedBox(height: 24),

                  // BOTÓN TOMAR FOTO
                  FilledButton.icon(
                    onPressed: _takePhoto,
                    icon: const Icon(Icons.camera_alt_outlined),
                    label: const Text('Tomar foto'),
                  ),

                  const SizedBox(height: 12),

                  // BOTÓN SUBIR DOCUMENTO
                  FilledButton.icon(
                    onPressed: _pickDocument,
                    icon: const Icon(Icons.upload_file),
                    label: const Text('Subir documento'),
                  ),
                ],
              ),
      ),
    );
  }
}
