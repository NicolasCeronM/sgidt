import 'package:flutter/material.dart';
import 'package:sgidt_mobile/core/api/api_result.dart';
import 'package:sgidt_mobile/services/password_reset_service.dart';

class ResetPasswordScreen extends StatefulWidget {
  final String email;
  const ResetPasswordScreen({super.key, required this.email});

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  final _passwordResetService = PasswordResetService();
  final _formKey = GlobalKey<FormState>();
  final _codeController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isLoading = false;
  bool _isPasswordHidden = true;
  bool _isPasswordEnabled = false;
  bool _isCodeVerifying = false;

  @override
  void initState() {
    super.initState();
    _codeController.addListener(_onCodeChanged);
  }

  @override
  void dispose() {
    _codeController.removeListener(_onCodeChanged);
    _codeController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _onCodeChanged() {
    if (_codeController.text.length == 6) {
      _verifyCode();
    } else {
      if (_isPasswordEnabled) setState(() => _isPasswordEnabled = false);
    }
  }

  Future<void> _verifyCode() async {
    FocusScope.of(context).unfocus();
    setState(() => _isCodeVerifying = true);

    final result = await _passwordResetService.verifyPasswordResetCode(widget.email, _codeController.text.trim());

    if (!mounted) return;
    
    switch (result) {
      case Success():
        setState(() => _isPasswordEnabled = true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Código verificado. Ingresa tu nueva contraseña."), backgroundColor: Colors.green),
        );
        break;
      case Failure(error: final e):
        setState(() => _isPasswordEnabled = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.red),
        );
        break;
    }

    setState(() => _isCodeVerifying = false);
  }

  Future<void> _submitResetPassword() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);

    final result = await _passwordResetService.setNewPassword(
      email: widget.email,
      code: _codeController.text.trim(),
      newPassword: _passwordController.text,
    );

    if (!mounted) return;
    
    switch (result) {
      case Success():
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("¡Contraseña actualizada con éxito!"), backgroundColor: Colors.green),
        );
        Navigator.of(context).popUntil((route) => route.isFirst);
        break;
      case Failure(error: final e):
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.red),
        );
        break;
    }
    
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Restablecer Contraseña")),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            Text("Se envió un código a ${widget.email}.", textAlign: TextAlign.center),
            const SizedBox(height: 24),
            TextFormField(
              controller: _codeController,
              decoration: InputDecoration(
                labelText: 'Código de 6 dígitos',
                prefixIcon: const Icon(Icons.pin_outlined),
                border: const OutlineInputBorder(),
                suffixIcon: _isCodeVerifying
                    ? const Padding(
                        padding: EdgeInsets.all(12.0),
                        child: CircularProgressIndicator(strokeWidth: 3),
                      )
                    : null,
              ),
              keyboardType: TextInputType.number,
              maxLength: 6,
              validator: (value) {
                if (value == null || value.length != 6) {
                  return 'Ingresa el código de 6 dígitos';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _passwordController,
              enabled: _isPasswordEnabled,
              obscureText: _isPasswordHidden,
              decoration: InputDecoration(
                labelText: 'Nueva Contraseña',
                prefixIcon: const Icon(Icons.lock_outline),
                border: const OutlineInputBorder(),
                suffixIcon: IconButton(
                  icon: Icon(_isPasswordHidden ? Icons.visibility_off : Icons.visibility),
                  onPressed: _isPasswordEnabled
                      ? () => setState(() => _isPasswordHidden = !_isPasswordHidden)
                      : null,
                ),
              ),
              validator: (value) {
                if (!_isPasswordEnabled) return null;
                if (value == null || value.length < 8) {
                  return 'Debe tener al menos 8 caracteres';
                }
                return null;
              },
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _isLoading || !_isPasswordEnabled ? null : _submitResetPassword,
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: _isLoading
                  ? const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 3, color: Colors.white),
                    )
                  : const Text("Restablecer Contraseña"),
            ),
          ],
        ),
      ),
    );
  }
}