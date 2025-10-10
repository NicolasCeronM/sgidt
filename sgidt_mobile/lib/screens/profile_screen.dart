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
    final u = await TokenStorage.getUser();
    final e = await TokenStorage.getEmpresas();
    final sel = await TokenStorage.getEmpresaSeleccionada();
    setState(() {
      _user = u;
      _empresas = e;
      _empresaSelId = sel ?? (e.isNotEmpty ? (e.first['empresa_id'] as int?) : null);
      _loading = false;
    });
  }

  // =========================
  // Helpers de presentación
  // =========================
  String _val(String key) => (_user?[key] ?? '').toString();

  String _iniciales() {
    final fn = (_user?['first_name'] ?? '').toString();
    final ln = (_user?['last_name'] ?? '').toString();
    final i1 = fn.isNotEmpty ? fn[0] : '';
    final i2 = ln.isNotEmpty ? ln[0] : '';
    final j = (i1 + i2).trim();
    if (j.isEmpty) {
      final backup = (_user?['email'] ?? _user?['username'] ?? '').toString();
      return backup.isNotEmpty ? backup[0].toUpperCase() : '?';
    }
    return j.toUpperCase();
  }

  Map<String, dynamic>? _empresaActual() {
    if (_empresaSelId == null) return null;
    try {
      return _empresas.firstWhere((e) => e['empresa_id'] == _empresaSelId);
    } catch (_) {
      return null;
    }
  }

  Widget _chipTipo() {
    final t = _val('tipo_contribuyente');
    if (t.isEmpty) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.blueGrey.withOpacity(0.10),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.blueGrey.withOpacity(0.25)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.verified_user, size: 16),
          const SizedBox(width: 6),
          Text(_titleCase(t)),
        ],
      ),
    );
  }

  static String _titleCase(String s) {
    if (s.isEmpty) return s;
    return s
        .split(RegExp(r'\s+|_+'))
        .map((w) => w.isEmpty ? '' : w[0].toUpperCase() + w.substring(1).toLowerCase())
        .join(' ');
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final empresa = _empresaActual();
    final fotoUrl = _user?['foto']?.toString();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Perfil'),
        actions: [
          IconButton(
            tooltip: 'Cerrar sesión',
            icon: const Icon(Icons.logout),
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
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              // ===== CABECERA =====
              Card(
                elevation: 0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      if (fotoUrl != null && fotoUrl.isNotEmpty && fotoUrl != 'null')
                        CircleAvatar(radius: 36, backgroundImage: NetworkImage(fotoUrl))
                      else
                        CircleAvatar(
                          radius: 36,
                          child: Text(
                            _iniciales(),
                            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                          ),
                        ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${_val('first_name')} ${_val('last_name')}'.trim(),
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                const Icon(Icons.mail, size: 16, color: Colors.grey),
                                const SizedBox(width: 6),
                                Flexible(child: Text(_val('email'))),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                _chipTipo(),
                                if (_val('rut').isNotEmpty)
                                  _Pill(icon: Icons.badge, label: 'RUT', value: _val('rut')),
                                if (_val('telefono').isNotEmpty)
                                  _Pill(icon: Icons.phone, label: 'Teléfono', value: _val('telefono')),
                                if (_val('region').isNotEmpty)
                                  _Pill(icon: Icons.map, label: 'Región', value: _val('region')),
                                if (_val('comuna').isNotEmpty)
                                  _Pill(icon: Icons.location_on, label: 'Comuna', value: _val('comuna')),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // ===== DETALLE DE CUENTA =====
              _SectionCard(
                title: 'Cuenta',
                children: [
                  _ItemRow(icon: Icons.alternate_email, label: 'Email', value: _val('email')),
                  _ItemRow(
                    icon: Icons.verified,
                    label: 'Activo',
                    value: (_user?['is_active'] == true) ? 'Sí' : 'No',
                  ),
                ],
              ),

              const SizedBox(height: 16),

              // ===== EMPRESA =====
              _SectionCard(
                title: 'Empresa',
                trailing: _empresas.length > 1
                    ? DropdownButton<int>(
                        value: _empresaSelId,
                        onChanged: (val) async {
                          if (val == null) return;
                          await TokenStorage.setEmpresaSeleccionada(val);
                          setState(() => _empresaSelId = val);
                        },
                        items: _empresas.map((e) {
                          final id = e['empresa_id'] as int;
                          return DropdownMenuItem<int>(
                            value: id,
                            child: Text('${e['empresa_nombre']} (${e['rol']})'),
                          );
                        }).toList(),
                      )
                    : null,
                children: [
                  if (empresa == null)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 8.0),
                      child: Text('Sin empresa seleccionada'),
                    )
                  else ...[
                    _ItemRow(icon: Icons.apartment, label: 'Nombre', value: '${empresa['empresa_nombre'] ?? ''}'),
                    _ItemRow(icon: Icons.workspace_premium, label: 'Rol', value: '${empresa['rol'] ?? ''}'),
                    if ((empresa['giro'] ?? '').toString().isNotEmpty)
                      _ItemRow(icon: Icons.category_outlined, label: 'Giro', value: '${empresa['giro']}'),
                    if ((empresa['emailContacto'] ?? '').toString().isNotEmpty)
                      _ItemRow(icon: Icons.email_outlined, label: 'Email contacto', value: '${empresa['emailContacto']}'),
                    if ((empresa['telefono'] ?? '').toString().isNotEmpty)
                      _ItemRow(icon: Icons.call_outlined, label: 'Teléfono', value: '${empresa['telefono']}'),
                    if ((empresa['direccion'] ?? '').toString().isNotEmpty)
                      _ItemRow(icon: Icons.place_outlined, label: 'Dirección', value: '${empresa['direccion']}'),
                    if ((empresa['comuna'] ?? '').toString().isNotEmpty)
                      _ItemRow(icon: Icons.location_city, label: 'Comuna', value: '${empresa['comuna']}'),
                    if ((empresa['region'] ?? '').toString().isNotEmpty)
                      _ItemRow(icon: Icons.public, label: 'Región', value: '${empresa['region']}'),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// =========================
// Widgets reutilizables
// =========================

class _SectionCard extends StatelessWidget {
  final String title;
  final List<Widget> children;
  final Widget? trailing;

  const _SectionCard({
    required this.title,
    required this.children,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                const Spacer(),
                if (trailing != null) trailing!,
              ],
            ),
            const SizedBox(height: 8),
            ...children,
          ],
        ),
      ),
    );
  }
}

class _ItemRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _ItemRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey[600]);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: Colors.grey[700]),
          const SizedBox(width: 10),
          SizedBox(width: 130, child: Text(label, style: muted)),
          const SizedBox(width: 8),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _Pill({required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.04),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.black.withOpacity(0.08)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14),
          const SizedBox(width: 6),
          Text('$label: ', style: const TextStyle(fontWeight: FontWeight.w600)),
          Text(value),
        ],
      ),
    );
  }
}
