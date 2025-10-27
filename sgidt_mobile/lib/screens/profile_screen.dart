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
    if (!mounted) return; // Evita error si el widget se desmonta
    setState(() => _loading = true);
    try {
      final u = await TokenStorage.getUser();
      final e = await TokenStorage.getEmpresas();
      final sel = await TokenStorage.getEmpresaSeleccionada();
      if (mounted) {
        setState(() {
          _user = u;
          _empresas = e;
          // Si no hay seleccionada, usa la primera si existe
          _empresaSelId = sel ?? (e.isNotEmpty ? (e.first['empresa_id'] as int?) : null);
          _loading = false;
        });
      }
    } catch (e) {
      if(mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al cargar datos del perfil: ${e.toString()}'))
        );
      }
    }
  }

  // --- Helpers de Datos ---
  String _val(String key) => (_user?[key] ?? '').toString();
  String _nombreCompleto() {
    final nombre = _val('first_name');
    final apellido = _val('last_name');
    if (nombre.isNotEmpty && apellido.isNotEmpty) {
      return '$nombre $apellido';
    } else if (nombre.isNotEmpty) {
      return nombre;
    } else {
      return 'Usuario'; // Fallback
    }
  }

  Map<String, dynamic>? _empresaActual() {
    if (_empresaSelId == null) return null;
    return _empresas.firstWhere((e) => e['empresa_id'] == _empresaSelId, orElse: () => {});
  }

  Future<void> _changeEmpresa(int? newId) async {
    if (newId == null || newId == _empresaSelId) return;
    setState(() => _empresaSelId = newId);
    await TokenStorage.setEmpresaSeleccionada(newId);
    // Opcional: Mostrar confirmación
    if(mounted) {
       ScaffoldMessenger.of(context).showSnackBar(
         const SnackBar(content: Text('Empresa activa cambiada.'), duration: Duration(seconds: 1)),
       );
    }
  }

  Future<void> _logout() async {
    // Mostrar diálogo de confirmación
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmar Cierre de Sesión'),
        content: const Text('¿Estás seguro de que deseas cerrar sesión?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Cerrar Sesión'),
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await AuthService.logout();
      if (!mounted) return;
      // Navegar a la pantalla de login y eliminar historial
      Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
    }
  }


  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi Perfil'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator( // Para recargar datos al deslizar hacia abajo
              onRefresh: _load,
              child: ListView( // Usamos ListView para mejor scroll si hay más contenido
                padding: const EdgeInsets.all(16.0),
                children: [
                  // --- Sección Header (Avatar y Nombre) ---
                  _buildProfileHeader(context),
                  const SizedBox(height: 24),
                  const Divider(),
                  const SizedBox(height: 16),

                  // --- Sección Información (RUT y Email) ---
                  _buildInfoSection(context),
                  const SizedBox(height: 16),
                  const Divider(),
                  const SizedBox(height: 16),

                  // --- Sección Empresa ---
                  _buildCompanySection(context),
                  const SizedBox(height: 32),

                  // --- Botón Cerrar Sesión ---
                  Center(
                    child: FilledButton.tonalIcon(
                      icon: const Icon(Icons.logout_rounded),
                      label: const Text('Cerrar Sesión'),
                      onPressed: _logout,
                      style: FilledButton.styleFrom(
                        foregroundColor: theme.colorScheme.error,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20), // Espacio al final
                ],
              ),
            ),
    );
  }

  // --- WIDGETS DE SECCIONES ---

  Widget _buildProfileHeader(BuildContext context) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;
    final nombre = _nombreCompleto();
    final inicial = nombre.isNotEmpty ? nombre[0].toUpperCase() : '?';

    return Column(
      children: [
        CircleAvatar(
          radius: 45,
          backgroundColor: theme.colorScheme.primaryContainer,
          child: Text(
            inicial,
            style: textTheme.headlineLarge?.copyWith(
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onPrimaryContainer,
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text(
          nombre,
          style: textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 4),
        Text(
          _val('cargo') == 'admin' ? 'Administrador' : 'Usuario', // Ejemplo, ajusta la lógica si tienes roles
          style: textTheme.bodyLarge?.copyWith(color: theme.colorScheme.secondary),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildInfoSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
         Padding(
          padding: const EdgeInsets.only(bottom: 8.0, left: 16),
          child: Text(
            'Información Personal',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
          ),
        ),
        Card( // Envuelve en Card para un look más definido
          elevation: 0,
          color: Theme.of(context).colorScheme.surfaceContainerLowest, // Color sutil
          child: Column(
            children: [
              _InfoTile(
                icon: Icons.badge_outlined,
                title: 'RUT',
                subtitle: _val('rut').isNotEmpty ? _val('rut') : 'No disponible',
              ),
              const Divider(height: 1, indent: 16, endIndent: 16),
              _InfoTile(
                icon: Icons.email_outlined,
                title: 'Email',
                subtitle: _val('email').isNotEmpty ? _val('email') : 'No disponible',
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildCompanySection(BuildContext context) {
     final nombreEmpresaActual = _empresaActual()?['nombre_empresa']?.toString() ?? 'Selecciona...';

     return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
       children: [
         Padding(
          padding: const EdgeInsets.only(bottom: 8.0, left: 16),
          child: Text(
            'Empresa',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
          ),
        ),
         Card( // Envuelve en Card
          elevation: 0,
          color: Theme.of(context).colorScheme.surfaceContainerLowest,
           child: ListTile(
             leading: const Icon(Icons.business_center_outlined),
             title: const Text('Empresa activa'),
             // Muestra el Dropdown directamente en el trailing
             trailing: _empresas.isEmpty
                 ? Text('Ninguna', style: TextStyle(color: Theme.of(context).colorScheme.outline))
                 : DropdownButtonHideUnderline( // Oculta la línea default
                     child: DropdownButton<int>(
                       value: _empresaSelId,
                       items: _empresas.map((emp) {
                         return DropdownMenuItem<int>(
                           value: emp['empresa_id'] as int?,
                           child: Text(
                            (emp['nombre_empresa'] ?? 'Sin nombre').toString(),
                             overflow: TextOverflow.ellipsis,
                           ),
                         );
                       }).toList(),
                       onChanged: _changeEmpresa,
                       // Estilo para que parezca parte del ListTile
                       style: Theme.of(context).textTheme.bodyMedium,
                       icon: const Icon(Icons.arrow_drop_down),
                       isDense: true, // Reduce el padding vertical
                     ),
                   ),
             contentPadding: const EdgeInsets.symmetric(horizontal: 16.0),
           ),
         ),
       ],
     );
  }
}

// --- WIDGETS AUXILIARES ---

// ListTile personalizado para mostrar info (RUT, Email)
class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const _InfoTile({required this.icon, required this.title, required this.subtitle});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title, style: Theme.of(context).textTheme.bodySmall),
      subtitle: Text(
        subtitle,
        style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w500),
      ),
      dense: true,
      visualDensity: VisualDensity.compact,
    );
  }
}

// Ya no usamos _InfoChip ni _CompanyDropdown directamente en el body