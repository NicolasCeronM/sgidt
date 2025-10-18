import 'package:flutter/material.dart';
import 'dart:convert'; 
import 'package:http/http.dart' as http; 

class RecoverPasswordScreen extends StatefulWidget {
  const RecoverPasswordScreen({super.key});

  @override
  State<RecoverPasswordScreen> createState() => _RecoverPasswordScreenState();
}

class _RecoverPasswordScreenState extends State<RecoverPasswordScreen> {
  // --- ¡INTERRUPTOR PRINCIPAL! ---
  // Cambia esto a 'false' para conectar al endpoint real.
  final bool _useMockData = true; 
  // ---
  
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _submitRecoveryRequest() async {
    if (!_formKey.currentState!.validate()) {
      return; 
    }
    FocusScope.of(context).unfocus();
    setState(() => _isLoading = true);

    try {
      if (_useMockData) {
        // --- LÓGICA DE SIMULACIÓN (MOCK) ---
        await Future.delayed(const Duration(seconds: 2));
        if (_emailController.text == "error@test.com") {
          throw Exception("Email no encontrado");
        }
      } else {
        // --- LÓGICA DE ENDPOINT (REAL) ---
        final url = Uri.parse('https://api.tu-dominio.com/auth/recover-password'); // <-- TU ENDPOINT 1
        
        final response = await http.post(
          url,
          headers: {'Content-Type': 'application/json; charset=UTF-8'},
          body: jsonEncode({'email': _emailController.text}),
        ).timeout(const Duration(seconds: 10));

        if (!mounted) return;

        if (response.statusCode != 200) {
          String errorMessage = "Error (${response.statusCode})";
          try {
            final responseBody = jsonDecode(response.body);
            // Ajusta 'error' o 'message' a la clave que usa tu API
            errorMessage = responseBody['error'] ?? responseBody['message'] ?? errorMessage;
          } catch (_) {}
          throw Exception(errorMessage);
        }
      }

      // --- ¡CAMBIO IMPORTANTE AQUÍ! ---
      // En lugar de volver al login, navegamos a la pantalla de reseteo.
      // Usamos 'pushReplacementNamed' para que el usuario no pueda "volver"
      // a esta pantalla de email.
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(
        '/reset-password',
        arguments: _emailController.text, // <-- Pasamos el email a la siguiente pantalla
      );
      // ------------------------------------

    } catch (e) {
      if (mounted) {
        _showFeedback("Error: ${e.toString()}", isError: true);
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _showFeedback(String message, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError
            ? Theme.of(context).colorScheme.error
            : Theme.of(context).colorScheme.primary,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Recuperar Contraseña"),
        centerTitle: true,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(24.0),
          children: [
            Text(
              "Ingresa tu email registrado",
              style: textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              "Te enviaremos un código de 6 dígitos para restablecer tu contraseña.", // <-- Texto actualizado
              style: textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            TextFormField(
              controller: _emailController,
              decoration: const InputDecoration(
                labelText: "Email",
                prefixIcon: Icon(Icons.email_outlined),
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.emailAddress,
              autocorrect: false,
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Por favor, ingresa tu email';
                }
                if (!RegExp(r'\S+@\S+\.\S+').hasMatch(value)) {
                  return 'Por favor, ingresa un email válido';
                }
                return null;
              },
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _isLoading ? null : _submitRecoveryRequest,
              icon: _isLoading ? Container() : const Icon(Icons.send_outlined),
              label: _isLoading
                  ? const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 3, color: Colors.white),
                    )
                  : const Text("Enviar código"), // <-- Texto actualizado
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}