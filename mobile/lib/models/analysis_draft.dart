import '../utils/fabric_parser.dart';

class AnalysisDraft {
  AnalysisDraft({
    required this.extractedText,
    required this.fabrics,
    this.brand = '',
    this.price = '',
    this.imagePath,
    this.productName = '',
    this.sourceUrl = '',
    this.notes = '',
  });

  final String extractedText;
  final String? imagePath;
  String brand;
  String price;
  String productName;
  String sourceUrl;
  String notes;
  Map<String, int> fabrics;

  AnalysisDraft copy() {
    return AnalysisDraft(
      extractedText: extractedText,
      imagePath: imagePath,
      brand: brand,
      price: price,
      productName: productName,
      sourceUrl: sourceUrl,
      notes: notes,
      fabrics: Map<String, int>.from(fabrics),
    );
  }

  double get parsedPrice => double.tryParse(price.replaceAll(',', '.')) ?? 0;
}

AnalysisDraft draftFromText(String text, {String? imagePath}) {
  return AnalysisDraft(
    extractedText: text,
    imagePath: imagePath,
    fabrics: FabricParser.parse(text),
  );
}
