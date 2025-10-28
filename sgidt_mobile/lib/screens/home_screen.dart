import 'package:flutter/material.dart';
import 'document_detail_screen.dart'; 
import 'documentos_screen.dart'; 
import 'reportes_screen.dart';
import '../services/documents_service.dart';
import '../theme/theme_controller.dart';
import '../core/storage/token_storage.dart'; 

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = true;
  String _userName = "Usuario"; // Valor por defecto
  List<Map<String, String>> _recentDocs = [];

  @override
  void initState() {
    super.initState();
    // Cargar datos del usuario y de los documentos al iniciar
    _loadUser();
    _loadData();
  }

  /// Carga el nombre del usuario desde el storage
  Future<void> _loadUser() async {
    final user = await TokenStorage.getUser(); 
    if (mounted && user != null) {
      setState(() {
        _userName = user['first_name']?.toString() ?? 'Usuario';
      });
    }
  }

  /// Carga los documentos recientes desde la API
  Future<void> _loadData() async {
    if (mounted) setState(() => _isLoading = true);

    try {
      final allDocs = await DocumentsService.fetchRecent();
      if (mounted) {
        setState(() {
          _recentDocs = allDocs.take(3).toList(); 
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al cargar documentos: ${e.toString()}')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Home'),
        actions: [
          // Botón para cambiar el tema
          IconButton(
            icon: Icon(ThemeController.instance.isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined),
            onPressed: () => ThemeController.instance.cycleTheme(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData, // Permite "tirar para recargar"
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // --- Header de Bienvenida ---
                _WelcomeHeader(userName: _userName),
                const SizedBox(height: 24),

                // --- 💡 CAMBIO: Fila de Acciones (en lugar de GridView) ---
                Row(
                  children: [
                    Expanded(
                      child: _ActionCard(
                        title: 'Ver Documentos',
                        icon: Icons.article_outlined,
                        color: theme.colorScheme.secondaryContainer,
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const DocumentosScreen()),
                          );
                        },
                      ),
                    ),
                    const SizedBox(width: 16), // Espacio entre tarjetas
                    Expanded(
                      child: _ActionCard(
                        title: 'Ver Reportes',
                        icon: Icons.bar_chart_outlined,
                        color: theme.colorScheme.secondaryContainer,
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const ReportesScreen()),
                          );
                        },
                      ),
                    ),
                  ],
                ),
                // --- 💡 FIN DEL CAMBIO ---

                const SizedBox(height: 24),

                // --- Header de Documentos Recientes ---
                _RecentDocsHeader(
                  onSeeAll: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => const DocumentosScreen()),
                    );
                  },
                ),
                const SizedBox(height: 12),

                // --- Lista de Documentos Recientes ---
                _RecentDocsList(isLoading: _isLoading, recentDocs: _recentDocs),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// --- WIDGETS MEJORADOS ---

class _WelcomeHeader extends StatelessWidget {
  final String userName;
  const _WelcomeHeader({required this.userName});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // --- 💡 CAMBIO: Texto de bienvenida actualizado ---
                Text(
                  'Hola, Bienvenido Nuevamente',
                  style: textTheme.titleMedium?.copyWith(
                    color: theme.colorScheme.onPrimaryContainer,
                  ),
                ),
                // --- 💡 FIN DEL CAMBIO ---
                Text(
                  userName, // Nombre dinámico
                  style: textTheme.headlineMedium?.copyWith(
                    color: theme.colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.bold,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          CircleAvatar(
            radius: 30,
            backgroundColor: theme.colorScheme.primary,
            child: Icon(
              Icons.person_outline,
              size: 30,
              color: theme.colorScheme.onPrimary,
            ),
          )
        ],
      ),
    );
  }
}

class _ActionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _ActionCard({
    required this.title,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Card(
      elevation: 0,
      color: color,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            // 💡 CAMBIO: Ajuste para que el contenido se alinee arriba
            mainAxisAlignment: MainAxisAlignment.start,
            children: [
              Icon(
                icon,
                size: 32,
                color: theme.colorScheme.onSecondaryContainer,
              ),
              const SizedBox(height: 16), // Espacio entre ícono y texto
              Text(
                title,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: theme.colorScheme.onSecondaryContainer,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RecentDocsHeader extends StatelessWidget {
  final VoidCallback onSeeAll;
  const _RecentDocsHeader({required this.onSeeAll});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text(
          'Documentos Recientes',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
        ),
        TextButton(
          onPressed: onSeeAll,
          child: const Text('Ver todos'),
        ),
      ],
    );
  }
}

class _RecentDocsList extends StatelessWidget {
  final bool isLoading;
  final List<Map<String, String>> recentDocs;

  const _RecentDocsList({required this.isLoading, required this.recentDocs});

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(child: Padding(
        padding: EdgeInsets.symmetric(vertical: 32),
        child: CircularProgressIndicator(),
      ));
    }

    if (recentDocs.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 32),
          child: Text('No hay documentos recientes.'),
        )
      );
    }

    return Column(
      children: recentDocs.map((doc) {
        return _RecentDocItem(doc: doc);
      }).toList(),
    );
  }
}

class _RecentDocItem extends StatelessWidget {
  final Map<String, String> doc;

  const _RecentDocItem({required this.doc});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;

    final String docId = doc['id'] ?? '';
    // Usar 'proveedor_nombre' si existe, si no, 'proveedor'
    final String proveedor = doc['proveedor_nombre'] ?? doc['proveedor'] ?? 'Proveedor N/A';
    final String total = doc['total'] ?? 'N/A';
    final String estado = doc['estado'] ?? 'N/A';

    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 12),
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: theme.dividerColor.withOpacity(0.5)),
      ),
      child: ListTile(
        leading: Icon(Icons.receipt_long_outlined, color: theme.colorScheme.primary),
        title: Text(
          proveedor, 
          style: textTheme.titleSmall, 
          overflow: TextOverflow.ellipsis
        ),
        subtitle: Text('Total: $total', style: textTheme.bodyMedium),
        trailing: Chip(
          label: Text(estado),
          labelStyle: TextStyle(
            fontSize: 12, 
            fontWeight: FontWeight.w500,
            color: theme.colorScheme.onTertiaryContainer
          ),
          backgroundColor: theme.colorScheme.tertiaryContainer,
          side: BorderSide.none,
          padding: const EdgeInsets.symmetric(horizontal: 8),
          visualDensity: VisualDensity.compact,
        ),
        onTap: () {
          if (docId.isNotEmpty) {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => DocumentDetailScreen(documento: doc),
              ),
            );
          }
        },
      ),
    );
  }
}