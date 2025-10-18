import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ResetPasswordScreen extends StatefulWidget {
  // Recibirá el email de la pantalla anterior
  final String email;
  const ResetPasswordScreen({super.key, required this.email});

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  // --- INTERRUPTOR ---
  final bool _useMockData = true;
  // ---

  final _formKey = GlobalKey<FormState>();
  final _codeController = TextEditingController();
  final _passwordController = TextEditingController();
  
  bool _isLoading = false;
  bool _isPasswordHidden = true;
  
  // <-- 1. NUEVA VARIABLE DE ESTADO -->
  bool _isPasswordEnabled = false;

  @override
  void initState() {
    super.initState();
    // <-- 2. AÑADIR UN LISTENER AL CAMPO DE CÓDIGO -->
    // Cada vez que el usuario escriba en el campo de código,
    // se llamará a la función _updatePasswordState
    _codeController.addListener(_updatePasswordState);
  }

  /// Actualiza el estado del campo de contraseña
  void _updatePasswordState() {
    // Comprueba si el campo de código tiene texto
    final bool hasText = _codeController.text.isNotEmpty;
    
    // Si el estado actual es diferente al nuevo, actualiza la UI
    if (hasText != _isPasswordEnabled) {
      setState(() {
        _isPasswordEnabled = hasText;
      });
    }
  }

  @override
  void dispose() {
    // <-- 3. LIMPIAR EL LISTENER AL SALIR DE LA PANTALLA -->
    _codeController.removeListener(_updatePasswordState);
    _codeController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  /// Lógica para enviar el código y la nueva contraseña
  Future<void> _submitReset() async {
    // (La lógica de _submitReset se mantiene exactamente igual)
    if (!_formKey.currentState!.validate()) {
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() => _isLoading = true);

    try {
      final code = _codeController.text;
      final newPassword = _passwordController.text;

      if (_useMockData) {
        // --- LÓGICA DE SIMULACIÓN (MOCK) ---
        await Future.delayed(const Duration(seconds: 2));
        if (code != "123456") { // Código simulado
          throw Exception("Código de verificación incorrecto");
        }
      } else {
        // --- LÓGICA DE ENDPOINT (REAL) ---
        final url = Uri.parse('https://api.tu-dominio.com/auth/reset-password'); // <-- TU ENDPOINT 2
        
        final response = await http.post(
          url,
          headers: {'Content-Type': 'application/json; charset=UTF-8'},
          body: jsonEncode({
            'email': widget.email,
            'code': code,
            'new_password': newPassword,
          }),
        ).timeout(const Duration(seconds: 10));

        if (!mounted) return;
        if (response.statusCode != 200) {
          String errorMessage = "Error (${response.statusCode})";
          try {
            final responseBody = jsonDecode(response.body);
            errorMessage = responseBody['error'] ?? responseBody['message'] ?? "Código o email inválido";
          } catch (_) {}
          throw Exception(errorMessage);
        }
      }

      // --- ÉXITO (COMÚN A AMBOS) ---
      if (!mounted) return;
      _showFeedback("Contraseña actualizada con éxito.", isError: false);
      
      await Future.delayed(const Duration(seconds: 1));
      
      if (mounted) {
        Navigator.of(context).pushNamedAndRemoveUntil(
          '/login',
          (route) => false,
        );
      }

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
    // (Esta función se mantiene igual)
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError
            ? Theme.of(context).colorScheme.error
            : Colors.green[700],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Restablecer Contraseña"),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(24.0),
          children: [
            // (Textos de cabecera se mantienen igual)
            Text(
              "Verifica tu identidad",
              style: textTheme.headlineSmall,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              "Ingresa el código que enviamos a:",
              style: textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            Text(
              widget.email,
              style: textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),

            // --- Campo de Código ---
            TextFormField(
              controller: _codeController, // El listener está adjunto a este
              decoration: const InputDecoration(
                labelText: "Código de Verificación",
                prefixIcon: Icon(Icons.pin_outlined),
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Ingresa el código';
                }
                return null;
              },
            ),
            const SizedBox(height: 24),

            // --- Campo de Nueva Contraseña ---
            TextFormField(
              // <-- 4. USAR LA VARIABLE DE ESTADO AQUÍ -->
              enabled: _isPasswordEnabled, // Se habilita/deshabilita
              controller: _passwordController,
              obscureText: _isPasswordHidden,
              decoration: InputDecoration(
                labelText: "Nueva Contraseña",
                prefixIcon: const Icon(Icons.lock_outline),
                border: const OutlineInputBorder(),
                suffixIcon: IconButton(
                  // También deshabilita el botón de "ojo" si el campo está inactivo
                  icon: Icon(
                    _isPasswordHidden
                        ? Icons.visibility_off_outlined
                        : Icons.visibility_outlined,
                  ),
                  onPressed: _isPasswordEnabled 
                      ? () => setState(() => _isPasswordHidden = !_isPasswordHidden)
                      : null,
                ),
              ),
              validator: (value) {
                // La validación solo corre si el campo está habilitado
                if (!_isPasswordEnabled) return null; 
                
                if (value == null || value.isEmpty) {
                  return 'Ingresa tu nueva contraseña';
                }
                if (value.length < 8) {
                  return 'Debe tener al menos 8 caracteres';
                }
                return null;
              },
            ),
            const SizedBox(height: 24),
            
            // --- Botón de Envío ---
            FilledButton(
              // <-- 5. DESHABILITAR EL BOTÓN SI LA CONTRASEÑA NO ESTÁ HABILITADA -->
              onPressed: _isLoading || !_isPasswordEnabled ? null : _submitReset,
              child: _isLoading
                  ? const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 3, color: Colors.white),
                    )
                  : const Text("Restablecer Contraseña"),
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