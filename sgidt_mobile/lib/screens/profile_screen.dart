import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../theme/theme_controller.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // ---- Avatar + nombre ----
              CircleAvatar(
                radius: 45,
                backgroundColor: AppTheme.sgidtRed.withOpacity(.1),
                child: const Icon(Icons.person_rounded,
                    size: 48, color: Colors.black87),
              ),
              const SizedBox(height: 12),
              const Text(
                'Usuario SGIDT',
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 18,
                ),
              ),
              const SizedBox(height: 24),

              // ---- Sección Datos personales ----
              _ProfileSection(
                title: 'Datos personales',
                items: const [
                  _ProfileItem(label: 'Nombre', value: 'Nombre Ejemplo'),
                  _ProfileItem(label: 'RUT', value: '11.111.111-1'),
                  _ProfileItem(label: 'Tipo contribuyente', value: 'Empresa'),
                ],
              ),
              const SizedBox(height: 12),

              // ---- Sección Contacto ----
              _ProfileSection(
                title: 'Contacto',
                items: const [
                  _ProfileItem(label: 'Correo electrónico', value: 'usuario@correo.cl'),
                  _ProfileItem(label: 'Teléfono', value: '+56 9 1234 5678'),
                  _ProfileItem(label: 'Comuna', value: 'Santiago'),
                  _ProfileItem(label: 'Región', value: 'Metropolitana'),
                ],
              ),

              const SizedBox(height: 20),

              // ---- Switch modo oscuro (REAL, con persistencia) ----
              Card(
                elevation: 0.3,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: AnimatedBuilder(
                  animation: ThemeController.instance,
                  builder: (_, __) {
                    final isDark = ThemeController.instance.isDark;
                    return SwitchListTile(
                      title: const Text('Modo oscuro'),
                      value: isDark,
                      onChanged: (v) => ThemeController.instance.toggleDark(v),
                      inactiveThumbColor: color.onSurface.withOpacity(.6),
                      activeColor: AppTheme.sgidtRed,
                    );
                  },
                ),
              ),

              const SizedBox(height: 24),

              // ---- Cerrar sesión ----
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(48),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onPressed: () {
                  AuthService.logout();
                  Navigator.pushReplacementNamed(context, '/login');
                },
                icon: const Icon(Icons.logout_rounded),
                label: const Text('Cerrar sesión'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/* ===============================
 *  Widgets auxiliares de sección
 * =============================== */

class _ProfileSection extends StatelessWidget {
  final String title;
  final List<_ProfileItem> items;
  const _ProfileSection({required this.title, required this.items});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0.3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            for (var i = 0; i < items.length; i++) ...[
              items[i],
              if (i < items.length - 1)
                Divider(height: 14, color: Colors.grey.withOpacity(.3)),
            ],
          ],
        ),
      ),
    );
  }
}

class _ProfileItem extends StatelessWidget {
  final String label;
  final String value;
  const _ProfileItem({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: Colors.grey.shade700,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value.isEmpty ? '—' : value,
              textAlign: TextAlign.end,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
