import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const CircleAvatar(radius: 38, child: Icon(Icons.person, size: 38)),
            const SizedBox(height: 12),
            const Text('Usuario SGIDT', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
            const SizedBox(height: 24),
            SwitchListTile(
              title: const Text('Modo oscuro (próximamente)'),
              value: false,
              onChanged: (_) {},
            ),
            const Spacer(),
            OutlinedButton(
              onPressed: () {
                AuthService.logout();
                Navigator.pushReplacementNamed(context, '/login');
              },
              child: const Text('Cerrar sesión'),
            )
          ],
        ),
      ),
    );
  }
}
