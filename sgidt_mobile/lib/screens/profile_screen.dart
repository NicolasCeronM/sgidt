import 'package:flutter/material.dart';
import '../core/storage/token_storage.dart';
import '../services/auth_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic>? _user;
  List<Map<String, dynamic>> _empresas = [];
  int? _empresaSelId;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final u = await TokenStorage.getUser();
    final e = await TokenStorage.getEmpresas();
    final sel = await TokenStorage.getEmpresaSeleccionada();
    if (mounted) {
      setState(() {
        _user = u;
        _empresas = e;
        _empresaSelId = sel ?? (e.isNotEmpty ? (e.first['empresa_id'] as int?) : null);
        _loading = false;
      });
    }
  }

  // --- Helpers de Datos ---
  String _val(String key) => (_user?[key] ?? '').toString();
  
  Map<String, dynamic>? _empresaActual() {
    if (_empresaSelId == null || _empresas.isEmpty) return null;
    try {
      return _empresas.firstWhere((e) => e['empresa_id'] == _empresaSelId);
    } catch (_) {
      return null;
    }
  }

  String _iniciales() {
    final fn = _val('first_name');
    final ln = _val('last_name');
    if (fn.isEmpty && ln.isEmpty) {
      final email = _val('email');
      return email.isNotEmpty ? email[0].toUpperCase() : '?';
    }
    return ((fn.isNotEmpty ? fn[0] : '') + (ln.isNotEmpty ? ln[0] : '')).toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final empresa = _empresaActual();
    final fotoUrl = _user?['foto']?.toString();
    final nombreCompleto = '${_val('first_name')} ${_val('last_name')}'.trim();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Perfil'),
        centerTitle: false,
        actions: [
          IconButton(
            tooltip: 'Cerrar sesión',
            icon: const Icon(Icons.logout_outlined),
            onPressed: () async {
              await AuthService.logout();
              if (mounted) {
                Navigator.of(context).pushReplacementNamed('/login');
              }
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // --- Tarjeta de Cabecera de Usuario ---
            _HeaderCard(
              nombre: nombreCompleto,
              email: _val('email'),
              iniciales: _iniciales(),
              fotoUrl: (fotoUrl != null && fotoUrl != 'null') ? fotoUrl : null,
              rut: _val('rut'),
              telefono: _val('telefono'),
            ),
            const SizedBox(height: 24),

            // --- Sección de Cuenta ---
            _SectionCard(
              title: 'Detalles de la Cuenta',
              children: [
                _InfoTile(
                  icon: Icons.verified_user_outlined,
                  label: 'Estado',
                  value: (_user?['is_active'] == true) ? 'Activo' : 'Inactivo',
                ),
                _InfoTile(
                  icon: Icons.alternate_email_outlined,
                  label: 'Nombre de usuario',
                  value: _val('username'),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // --- Sección de Empresa ---
            _SectionCard(
              title: 'Empresa Actual',
              trailing: _empresas.length > 1
                  ? _CompanyDropdown(
                      empresas: _empresas,
                      selectedId: _empresaSelId,
                      onChanged: (val) async {
                        if (val == null) return;
                        await TokenStorage.setEmpresaSeleccionada(val);
                        setState(() => _empresaSelId = val);
                      },
                    )
                  : null,
              children: [
                if (empresa == null)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 16.0),
                    child: Center(child: Text('Sin empresa seleccionada')),
                  )
                else ...[
                  _InfoTile(icon: Icons.apartment_outlined, label: 'Nombre', value: '${empresa['empresa_nombre'] ?? ''}'),
                  _InfoTile(icon: Icons.work_outline_rounded, label: 'Rol', value: '${empresa['rol'] ?? ''}'),
                  _InfoTile(icon: Icons.location_on_outlined, label: 'Dirección', value: '${empresa['direccion'] ?? ''}'),
                  _InfoTile(icon: Icons.phone_outlined, label: 'Teléfono', value: '${empresa['telefono'] ?? ''}'),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// --- WIDGETS DE UI MEJORADOS ---

class _HeaderCard extends StatelessWidget {
  final String nombre, email, iniciales, rut, telefono;
  final String? fotoUrl;

  const _HeaderCard({
    required this.nombre, required this.email, required this.iniciales,
    required this.rut, required this.telefono, this.fotoUrl,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;
    // ✅ CORRECCIÓN: Determina si el tema actual es oscuro.
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Card(
      elevation: 0,
      // ✅ CORRECCIÓN: Usa un color diferente para el modo oscuro.
      color: isDark ? scheme.surfaceContainerHighest : scheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 32,
                  backgroundColor: scheme.primary,
                  foregroundColor: scheme.onPrimary,
                  backgroundImage: (fotoUrl != null) ? NetworkImage(fotoUrl!) : null,
                  child: (fotoUrl == null)
                      ? Text(iniciales, style: textTheme.headlineSmall?.copyWith(color: scheme.onPrimary))
                      : null,
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(nombre, style: textTheme.headlineSmall?.copyWith(color: isDark ? scheme.onSurface : scheme.onPrimaryContainer, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text(email, style: textTheme.bodyMedium?.copyWith(color: isDark ? scheme.onSurfaceVariant : scheme.onPrimaryContainer)),
                    ],
                  ),
                ),
              ],
            ),
            if (rut.isNotEmpty || telefono.isNotEmpty) ...[
              const Divider(height: 24),
              Wrap(
                spacing: 12,
                runSpacing: 8,
                alignment: WrapAlignment.center,
                children: [
                  if (rut.isNotEmpty) _InfoChip(icon: Icons.badge_outlined, text: rut),
                  if (telefono.isNotEmpty) _InfoChip(icon: Icons.phone_outlined, text: telefono),
                ],
              )
            ],
          ],
        ),
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final List<Widget> children;
  final Widget? trailing;

  const _SectionCard({required this.title, required this.children, this.trailing});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text(title, style: textTheme.titleMedium),
            const Spacer(),
            if (trailing != null) trailing!,
          ],
        ),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(children: children),
        ),
      ],
    );
  }
}

class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoTile({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    if (value.isEmpty || value == 'null') return const SizedBox.shrink();
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.onSurfaceVariant),
      title: Text(value),
      subtitle: Text(label),
      dense: true,
      visualDensity: VisualDensity.compact,
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String text;
  const _InfoChip({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Chip(
      avatar: Icon(icon, size: 18, color: isDark ? scheme.onSurfaceVariant : scheme.onSecondaryContainer),
      label: Text(text),
      backgroundColor: isDark ? scheme.surfaceContainer : scheme.secondaryContainer.withOpacity(0.4),
      side: BorderSide.none,
      padding: const EdgeInsets.symmetric(horizontal: 12),
    );
  }
}

class _CompanyDropdown extends StatelessWidget {
  final List<Map<String, dynamic>> empresas;
  final int? selectedId;
  final ValueChanged<int?> onChanged;

  const _CompanyDropdown({required this.empresas, this.selectedId, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return DropdownButton<int>(
      value: selectedId,
      onChanged: onChanged,
      underline: const SizedBox.shrink(),
      icon: const Icon(Icons.unfold_more_rounded),
      items: empresas.map((e) {
        final id = e['empresa_id'] as int;
        return DropdownMenuItem<int>(
          value: id,
          child: Text(e['empresa_nombre'] as String),
        );
      }).toList(),
    );
  }
}