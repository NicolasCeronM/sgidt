import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; 
import 'dart:math' as math; 

import '../services/auth_service.dart';
import '../core/api/api_exceptions.dart';
import '../widgets/primary_buttom.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _userCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _obscure = true;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _userCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final ok = _form.currentState?.validate() ?? false;
    if (!ok) return;
    setState(() {
      _loading = true;
      _error = null;
    });

    // No se necesita limpiar NADA.
    // Enviamos el texto tal cual (ej. "20399064-2" o "user@mail.com")
    // El backend (backend.py) se encarga de normalizar el RUT internamente.
    try {
      await AuthService.login(_userCtrl.text.trim(), _passCtrl.text);
      
      if (!mounted) return;
      Navigator.pushReplacementNamed(context, '/home');
    } on AuthException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = 'Algo salió mal. Por favor, inténtalo de nuevo.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;
    final colorScheme = theme.colorScheme;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _form,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // --- Logo ---
                    const _Logo(),
                    const SizedBox(height: 24),
                    Text(
                      'Iniciar sesión',
                      textAlign: TextAlign.center,
                      style: textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Bienvenido de vuelta a SGIDT Móvil',
                      textAlign: TextAlign.center,
                      style: textTheme.bodyLarge?.copyWith(color: colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 32),

                    // --- Mensaje de Error ---
                    if (_error != null) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(
                          color: colorScheme.errorContainer,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.error_outline, color: colorScheme.onErrorContainer),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                _error!,
                                style: textTheme.bodyMedium?.copyWith(color: colorScheme.onErrorContainer),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // --- Campo de Rut o Email ---
                    TextFormField(
                      controller: _userCtrl,
                      textInputAction: TextInputAction.next,
                      autocorrect: false,
                      keyboardType: TextInputType.visiblePassword, 
                      inputFormatters: [
                        RutGuionInputFormatter(), // 💡 CAMBIADO AL NUEVO FORMATEADOR
                      ],
                      decoration: const InputDecoration(
                        labelText: 'rut o email',
                        prefixIcon: Icon(Icons.person_outline_rounded),
                        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
                      ),
                      validator: (v) => (v == null || v.trim().isEmpty) ? 'Ingresa tu rut o email' : null,
                    ),
                    const SizedBox(height: 16),

                    // --- Campo de Contraseña ---
                    TextFormField(
                      controller: _passCtrl,
                      obscureText: _obscure,
                      onFieldSubmitted: (_) => _submit(),
                      decoration: InputDecoration(
                        labelText: 'Contraseña',
                        prefixIcon: const Icon(Icons.lock_outline_rounded),
                        border: const OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
                        suffixIcon: IconButton(
                          onPressed: () => setState(() => _obscure = !_obscure),
                          icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                        ),
                      ),
                      validator: (v) => (v == null || v.isEmpty) ? 'Ingresa tu contraseña' : null,
                    ),
                    const SizedBox(height: 8),

                    // --- Olvidé mi Contraseña ---
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: () {
                          Navigator.of(context).pushNamed('/recover-password');
                        },
                        child: const Text('¿Olvidaste tu contraseña?'),
                      ),
                    ),
                    const SizedBox(height: 16),
                    
                    // --- Botón de Ingresar ---
                    PrimaryButton(
                      label: 'Ingresar',
                      isLoading: _loading,
                      onPressed: _submit,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// --- WIDGET DEL LOGO (Sin cambios) ---
class _Logo extends StatelessWidget {
  const _Logo();
  static const bool _useImageAsset = true;

  @override
  Widget build(BuildContext context) {
    if (_useImageAsset) {
      return Image.asset(
        'assets/logo_2.png', 
        height: 100,
      );
    } else {
      return CircleAvatar(
        radius: 48,
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        child: Text(
          'SGIDT',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onPrimaryContainer,
            fontWeight: FontWeight.w900,
            fontSize: 24,
          ),
        ),
      );
    }
  }
}


// 💡 INICIO NUEVO FORMATEADOR - RutGuionInputFormatter 💡
/// Formateador que aplica automáticamente el guion (-) antes del dígito 
/// verificador del RUT (XXXXXXXX-Y) mientras el usuario escribe.
/// Ignora el formato si detecta un '@', asumiendo que es un email.
class RutGuionInputFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(
      TextEditingValue oldValue, TextEditingValue newValue) {
    
    final newText = newValue.text;

    // Si es un email (contiene @), no hacer nada.
    if (newText.contains('@')) {
      return newValue;
    }

    // 1. Limpiar el texto: solo dígitos y k/K. Se eliminan también los guiones
    //    que el usuario pueda haber escrito para evitar duplicados.
    String cleanText = newText.replaceAll(RegExp(r'[^0-9kK]'), '').toUpperCase();

    // 2. Limitar a 9 caracteres (8 para el cuerpo + 1 para el DV)
    if (cleanText.length > 9) {
      cleanText = cleanText.substring(0, 9);
    }

    // 3. Si está vacío, retornar vacío
    if (cleanText.isEmpty) {
      return newValue.copyWith(text: '');
    }

    String formattedText;

    // 4. Lógica para añadir el guion
    if (cleanText.length > 1) {
      // Separar cuerpo y dígito verificador
      String dv = cleanText.substring(cleanText.length - 1);
      String body = cleanText.substring(0, cleanText.length - 1);
      // Combinar con el guion
      formattedText = '$body-$dv';
    } else {
      formattedText = cleanText;
    }

    // 5. Calcular la posición del cursor
    int selectionIndex = newValue.selection.end + (formattedText.length - newText.length);
    selectionIndex = math.max(0, math.min(selectionIndex, formattedText.length));

    return TextEditingValue(
      text: formattedText,
      selection: TextSelection.collapsed(offset: selectionIndex),
      composing: TextRange.empty,
    );
  }
}