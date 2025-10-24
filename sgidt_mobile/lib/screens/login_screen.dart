import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../core/api/api_exceptions.dart';

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

                    // --- Mensaje de Error Mejorado ---
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

                    // --- Campo de Usuario ---
                    TextFormField(
                      controller: _userCtrl,
                      textInputAction: TextInputAction.next,
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
                          // Navega a la pantalla de recuperación
                          Navigator.of(context).pushNamed('/recover-password');
                        },
                        child: const Text('¿Olvidaste tu contraseña?'),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // --- Botón de Ingresar ---
                    SizedBox(
                      height: 52,
                      child: FilledButton(
                        onPressed: _loading ? null : _submit,
                        style: FilledButton.styleFrom(
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: _loading
                            ? const SizedBox(
                                width: 24, height: 24,
                                child: CircularProgressIndicator(strokeWidth: 3, color: Colors.white),
                              )
                            : const Text('Ingresar', style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
                    ),

                    // --- Mensaje para Desarrolladores (solo en modo debug) ---
                    //if (kDebugMode) ...[
                      //const SizedBox(height: 24),
                     // Text(
                      //  'Si estás en dispositivo físico y tu API corre en el PC,\nrecuerda ejecutar:  adb reverse tcp:8000 tcp:8000',
                      //  textAlign: TextAlign.center,
                      //  style: textTheme.bodySmall?.copyWith(color: theme.hintColor), 
                    //  ),
                   // ],
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

/// Widget para el logo. Edita aquí para cambiar entre un logo de texto
/// o una imagen desde tus assets.
class _Logo extends StatelessWidget {
  const _Logo();

  // ✅ CAMBIA ESTO A `true` PARA USAR UNA IMAGEN DE LOGO
  static const bool _useImageAsset = true;

  @override
  Widget build(BuildContext context) {
    if (_useImageAsset) {
      // Si usas una imagen, asegúrate de haberla añadido en pubspec.yaml
      // y de que la ruta 'assets/logo.png' es correcta.
      return Image.asset(
        'assets/logo_2.png', // Reemplaza con la ruta de tu logo
        height: 100,
      );
    } else {
      // Versión de texto como fallback o placeholder.
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