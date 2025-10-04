import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final email = TextEditingController();
  final pass = TextEditingController();

  bool loading = false;
  bool obscure = true;
  String? error;

  Future<void> _login() async {
    final formOk = _formKey.currentState?.validate() ?? false;
    if (!formOk) return;

    setState(() { loading = true; error = null; });
    final ok = await AuthService.login(email.text.trim(), pass.text);
    setState(() => loading = false);

    if (ok && mounted) {
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      setState(() => error = 'Credenciales inválidas. Revisa usuario/contraseña.');
    }
  }

  void _forgot() {
    // TODO: navegar a tu flujo real de recuperación
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Función de recuperación próximamente')),
    );
  }

  void _signup() {
    // TODO: navegar a registro si lo tienes
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Registro próximamente')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      // quitamos AppBar para un look más limpio
      body: Stack(
        children: [
          // HEADER con onda/curva
          _Header(),

          // CONTENIDO
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 140, 20, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Título + subtítulo
                  Text(
                    'LOGIN',
                    style: TextStyle(
                      color: cs.onSurface,
                      fontSize: 28,
                      fontWeight: FontWeight.w900,
                      letterSpacing: .3,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Ingresa con tu correo/RUT y contraseña\npara sincronizar tus documentos.',
                    style: TextStyle(color: Colors.grey.shade700),
                  ),
                  const SizedBox(height: 22),

                  if (error != null) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      decoration: BoxDecoration(
                        color: AppTheme.err.withOpacity(.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppTheme.err.withOpacity(.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.error_outline, color: AppTheme.err),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              error!,
                              style: const TextStyle(color: AppTheme.err, fontWeight: FontWeight.w600),
                            ),
                          ),
                          IconButton(
                            onPressed: () => setState(() => error = null),
                            icon: const Icon(Icons.close, size: 18, color: AppTheme.err),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],

                  // FORM
                  Form(
                    key: _formKey,
                    child: Column(
                      children: [
                        TextFormField(
                          controller: email,
                          keyboardType: TextInputType.emailAddress,
                          decoration: const InputDecoration(
                            labelText: 'Email o RUT',
                            prefixIcon: Icon(Icons.person_outline),
                          ),
                          validator: (v) {
                            if (v == null || v.trim().isEmpty) {
                              return 'Ingresa tu email o RUT';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 12),
                        TextFormField(
                          controller: pass,
                          obscureText: obscure,
                          decoration: InputDecoration(
                            labelText: 'Contraseña',
                            prefixIcon: const Icon(Icons.lock_outline),
                            suffixIcon: IconButton(
                              onPressed: () => setState(() => obscure = !obscure),
                              icon: Icon(obscure ? Icons.visibility_off : Icons.visibility),
                              tooltip: obscure ? 'Mostrar' : 'Ocultar',
                            ),
                          ),
                          validator: (v) {
                            if (v == null || v.isEmpty) return 'Ingresa tu contraseña';
                            if (v.length < 4) return 'Mínimo 4 caracteres';
                            return null;
                          },
                        ),
                        const SizedBox(height: 12),
                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                            onPressed: _forgot,
                            child: const Text('¿Olvidaste tu contraseña?'),
                          ),
                        ),
                        const SizedBox(height: 8),
                        // BOTÓN grande
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: loading ? null : _login,
                            style: ElevatedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                            ),
                            child: loading
                                ? const SizedBox(
                                    height: 20, width: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                  )
                                : const Text('Ingresar', style: TextStyle(fontWeight: FontWeight.w800)),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 22),

                  // Divider sutil
                  Row(
                    children: [
                      Expanded(child: Divider(color: Colors.grey.shade300)),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        child: Text('o', style: TextStyle(color: Colors.grey.shade600)),
                      ),
                      Expanded(child: Divider(color: Colors.grey.shade300)),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Enlaces secundarios
                  Center(
                    child: Column(
                      children: [
                        Text('¿Aún no tienes cuenta?', style: TextStyle(color: Colors.grey.shade700)),
                        TextButton(
                          onPressed: _signup,
                          child: const Text('Crear cuenta'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Overlay de carga (evita toques mientras loguea)
          if (loading)
            Positioned.fill(
              child: ColoredBox(
                color: Colors.black.withOpacity(.04),
                child: const Center(child: CircularProgressIndicator()),
              ),
            ),
        ],
      ),
    );
  }
}

/// Header con pequeño degradado y esquina redondeada inferior
class _Header extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    const purpleDeep = Color(0xFF2A1140);
    const purple = Color(0xFF4A1D6A);

    return SizedBox(
      height: 120,
      child: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [purpleDeep, purple],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(24),
                bottomRight: Radius.circular(24),
              ),
            ),
          ),
          // Circulitos decorativos sutiles
          Positioned(
            left: -30,
            top: 10,
            child: Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(.06),
                shape: BoxShape.circle,
              ),
            ),
          ),
          Positioned(
            right: -20,
            top: -10,
            child: Container(
              width: 110,
              height: 110,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(.06),
                shape: BoxShape.circle,
              ),
            ),
          ),
          // Logo/título opcional
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              child: Row(
                children: const [
                  Icon(Icons.lock_outline, color: Colors.white),
                  SizedBox(width: 8),
                  Text('Acceso SGIDT',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
