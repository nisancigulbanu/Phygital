import 'package:flutter/material.dart';

import '../models/analysis_result.dart';
import '../utils/fabric_parser.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({
    super.key,
    required this.result,
    required this.brand,
    required this.price,
  });

  final AnalysisResult result;
  final String brand;
  final String price;

  Color _qualityColor(String quality) {
    switch (quality) {
      case 'iyi':
        return const Color(0xFF2D8A55);
      case 'kotu':
        return const Color(0xFFC04B42);
      default:
        return const Color(0xFFC98C2E);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Analiz Sonucu')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: _qualityColor(result.quality).withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      result.quality.toUpperCase(),
                      style: TextStyle(
                        color: _qualityColor(result.quality),
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      if (result.productName.isNotEmpty)
                        Text(
                          result.productName,
                          textAlign: TextAlign.right,
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                      Text(brand.isEmpty ? 'Marka girilmedi' : brand),
                      Text(price.isEmpty ? 'Fiyat girilmedi' : '$price TL'),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Kumas Dagilimi', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 12),
                  ...result.fabric.entries.map(
                    (entry) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Row(
                        children: [
                          SizedBox(width: 96, child: Text(FabricParser.displayLabel(entry.key))),
                          Expanded(
                            child: LinearProgressIndicator(
                              value: entry.value / 100,
                              minHeight: 10,
                              borderRadius: BorderRadius.circular(999),
                              backgroundColor: const Color(0xFFEAE3D4),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Text('%${entry.value}'),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Marka Etik Skoru', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  Text(
                    result.ecoScore == null ? 'Bilinmiyor' : '${result.ecoScore}/10',
                    style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('AI Onerisi', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 12),
                  Text(result.recommendation, style: const TextStyle(height: 1.5)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
