import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../models/analysis_draft.dart';
import '../models/analysis_result.dart';
import '../models/product_lookup_result.dart';
import '../utils/fabric_parser.dart';

class ApiService {
  ApiService({http.Client? client})
      : _client = client ?? http.Client(),
        _baseUrl = _resolveBaseUrl();

  final http.Client _client;
  final String _baseUrl;

  static String _resolveBaseUrl() {
    const configured = String.fromEnvironment('API_BASE_URL');
    if (configured.isNotEmpty) {
      return configured;
    }
    if (kIsWeb) {
      return 'http://127.0.0.1:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  Future<AnalysisResult> analyze({
    required String userId,
    required String brand,
    required double price,
    required Map<String, int> fabrics,
    String productName = '',
    String sourceUrl = '',
  }) async {
    final response = await _client.post(
      Uri.parse('$_baseUrl/analyze'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'user_id': userId,
        'brand': brand,
        'price': price,
        'fabrics': fabrics,
        'product_name': productName,
        'source_url': sourceUrl,
      }),
    );

    if (response.statusCode != 200) {
      throw ApiException(_readErrorMessage(response, fallback: 'Analiz alinamadi.'));
    }

    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    return AnalysisResult.fromJson(decoded);
  }

  Future<ProductLookupResult> extractProduct({
    required String productUrl,
  }) async {
    final response = await _client.post(
      Uri.parse('$_baseUrl/extract-product'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'product_url': productUrl,
      }),
    );

    if (response.statusCode != 200) {
      throw ApiException(_readErrorMessage(response, fallback: 'Urun bilgisi alinamadi.'));
    }

    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    return ProductLookupResult.fromJson(decoded);
  }

  Future<AnalysisDraft> scanLabelImage({
    required Uint8List imageBytes,
    String? imagePath,
  }) async {
    final response = await _client.post(
      Uri.parse('$_baseUrl/api/v1/scan'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'image': base64Encode(imageBytes)}),
    );

    if (response.statusCode != 200) {
      throw ApiException(_readErrorMessage(response, fallback: 'Etiket taranamadi.'));
    }

    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    final rawFabric = decoded['fabric_composition'] as Map<String, dynamic>? ?? {};
    final fabrics = rawFabric.map(
      (key, value) => MapEntry(
        FabricParser.normalizeFabricKey(key),
        (value as num?)?.round() ?? 0,
      ),
    );
    return AnalysisDraft(
      extractedText: decoded['raw_text'] as String? ?? '',
      fabrics: fabrics,
      brand: decoded['brand'] as String? ?? '',
      imagePath: imagePath,
      notes: 'OCR backend uzerinden tamamlandi. Oranlari gondermeden once hizlica kontrol edin.',
    );
  }

  String _readErrorMessage(http.Response response, {required String fallback}) {
    try {
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      final detail = decoded['detail'];
      if (detail is String && detail.isNotEmpty) {
        return detail;
      }
    } catch (_) {
      // Ignore invalid payloads and fall back to a generic message.
    }
    return '$fallback (${response.statusCode})';
  }
}

class ApiException implements Exception {
  ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}
