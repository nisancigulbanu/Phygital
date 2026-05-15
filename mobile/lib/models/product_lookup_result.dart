import 'analysis_draft.dart';

class ProductLookupResult {
  ProductLookupResult({
    required this.title,
    required this.brand,
    required this.price,
    required this.imageUrl,
    required this.fabrics,
    required this.extractedText,
    required this.notes,
  });

  final String title;
  final String brand;
  final double? price;
  final String imageUrl;
  final Map<String, int> fabrics;
  final String extractedText;
  final String notes;

  factory ProductLookupResult.fromJson(Map<String, dynamic> json) {
    final rawFabric = json['fabrics'] as Map<String, dynamic>? ?? {};
    return ProductLookupResult(
      title: json['title'] as String? ?? '',
      brand: json['brand'] as String? ?? '',
      price: (json['price'] as num?)?.toDouble(),
      imageUrl: json['image_url'] as String? ?? '',
      fabrics: rawFabric.map(
        (key, value) => MapEntry(key, (value as num?)?.round() ?? 0),
      ),
      extractedText: json['extracted_text'] as String? ?? '',
      notes: json['notes'] as String? ?? '',
    );
  }

  AnalysisDraft toDraft({required String sourceUrl}) {
    return AnalysisDraft(
      extractedText: extractedText,
      fabrics: fabrics,
      brand: brand,
      price: price?.toStringAsFixed(0) ?? '',
      productName: title,
      sourceUrl: sourceUrl,
      notes: notes,
    );
  }
}
