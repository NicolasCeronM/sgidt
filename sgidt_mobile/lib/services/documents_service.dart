class DocumentsService {
  static Future<List<Map<String, String>>> fetchRecent() async {
    await Future.delayed(const Duration(milliseconds: 400));
    return [
      {'id': '1', 'prov': 'Proveedor A', 'fecha': '04-10-2025', 'total': '\$120.000', 'estado': 'pendiente'},
      {'id': '2', 'prov': 'Proveedor B', 'fecha': '03-10-2025', 'total': '\$89.990',  'estado': 'validado'},
      {'id': '3', 'prov': 'Proveedor C', 'fecha': '02-10-2025', 'total': '\$45.500',  'estado': 'rechazado'},
    ];
  }

  static Future<Map<String, String>> fetchDetail(String id) async {
    await Future.delayed(const Duration(milliseconds: 300));
    return {
      'proveedor': 'Proveedor $id',
      'fecha': '04-10-2025',
      'folio': '12345678-9',
      'total': '\$120.000',
      'estado': id == '2' ? 'validado' : 'pendiente',
    };
  }
}
