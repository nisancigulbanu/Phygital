class AnalysisResult {
  AnalysisResult({
    required this.analysisId,
    required this.fabric,
    required this.quality,
    required this.recommendation,
    required this.productName,
    this.ecoScore,
  });

  final String analysisId;
  final Map<String, int> fabric;
  final String quality;
  final String recommendation;
  final String productName;
  final int? ecoScore;

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    final rawFabric = json['fabric'] as Map<String, dynamic>? ?? {};
    return AnalysisResult(
      analysisId: json['analysis_id'] as String? ?? '',
      fabric: rawFabric.map(
        (key, value) => MapEntry(key, (value as num?)?.round() ?? 0),
      ),
      quality: json['quality'] as String? ?? 'orta',
      ecoScore: (json['eco_score'] as num?)?.toInt(),
      recommendation: json['recommendation'] as String? ?? '',
      productName: json['product_name'] as String? ?? '',
    );
  }
}
