import 'package:flutter/material.dart';

import '../models/analysis_draft.dart';
import '../models/analysis_result.dart';
import '../services/api_service.dart';
import '../services/local_storage_service.dart';
import '../utils/fabric_parser.dart';
import 'result_screen.dart';

class ReviewScreen extends StatefulWidget {
  const ReviewScreen({super.key, required this.initialDraft});

  final AnalysisDraft initialDraft;

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  final _apiService = ApiService();
  final _storageService = LocalStorageService();
  final _brandController = TextEditingController();
  final _priceController = TextEditingController();
  late List<_FabricInputRow> _fabricRows;
  bool _isSubmitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _brandController.text = widget.initialDraft.brand;
    _priceController.text = widget.initialDraft.price;
    final entries = widget.initialDraft.fabrics.entries.where((entry) => entry.value > 0);
    _fabricRows = entries
        .map((entry) => _FabricInputRow(name: entry.key, percentage: entry.value.toString()))
        .toList();
    if (_fabricRows.isEmpty) {
      _fabricRows = [_FabricInputRow()];
    }
  }

  @override
  void dispose() {
    _brandController.dispose();
    _priceController.dispose();
    for (final row in _fabricRows) {
      row.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _isSubmitting = true;
      _error = null;
    });
    try {
      final userId = await _storageService.getOrCreateUserId();
      final fabrics = <String, int>{};
      for (final row in _fabricRows) {
        final normalizedKey = FabricParser.normalizeFabricKey(row.nameController.text);
        final value = int.tryParse(row.percentageController.text.trim());
        if (normalizedKey.isNotEmpty && value != null && value > 0) {
          fabrics[normalizedKey] = (fabrics[normalizedKey] ?? 0) + value;
        }
      }
      if (fabrics.isEmpty) {
        setState(() {
          _isSubmitting = false;
          _error = 'En az bir kumas ve oran girmeniz gerekiyor.';
        });
        return;
      }
      final total = fabrics.values.fold<int>(0, (sum, value) => sum + value);
      if (total != 100) {
        setState(() {
          _isSubmitting = false;
          _error = 'Kumas oranlarinin toplami %100 olmali. Su an toplam %$total.';
        });
        return;
      }

      final AnalysisResult result = await _apiService.analyze(
        userId: userId,
        brand: _brandController.text.trim(),
        price: double.tryParse(_priceController.text.replaceAll(',', '.')) ?? 0,
        fabrics: fabrics,
        productName: widget.initialDraft.productName,
        sourceUrl: widget.initialDraft.sourceUrl,
      );

      if (!mounted) {
        return;
      }
      setState(() => _isSubmitting = false);
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ResultScreen(
            result: result,
            brand: _brandController.text.trim(),
            price: _priceController.text.trim(),
          ),
        ),
      );
    } catch (_) {
      setState(() {
        _isSubmitting = false;
        _error = 'Backend ile iletisim kurulamadi. API adresini ve sunucunun acik oldugunu kontrol edin.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('OCR Sonucunu Kontrol Et')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (widget.initialDraft.productName.isNotEmpty) ...[
                      Text(
                        widget.initialDraft.productName,
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 8),
                    ],
                    if (widget.initialDraft.notes.isNotEmpty) ...[
                      Text(
                        widget.initialDraft.notes,
                        style: const TextStyle(height: 1.4, color: Colors.black54),
                      ),
                      const SizedBox(height: 12),
                    ],
                    const Text('Ham OCR Metni', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 12),
                    Text(
                      widget.initialDraft.extractedText.isEmpty
                          ? 'Metin bulunamadi. Oranlari asagidan elle girebilirsiniz.'
                          : widget.initialDraft.extractedText,
                      style: const TextStyle(height: 1.45),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _brandController,
              decoration: const InputDecoration(
                labelText: 'Marka',
                hintText: 'or. zara',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _priceController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Fiyat (TL)',
                hintText: 'or. 299',
              ),
            ),
            const SizedBox(height: 16),
            const Text('Kumas Oranlari', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            ..._buildFabricRows(),
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: _addFabricRow,
                icon: const Icon(Icons.add),
                label: const Text('Kumas Ekle'),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 4),
              Text(_error!, style: const TextStyle(color: Colors.redAccent)),
            ],
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _isSubmitting ? null : _submit,
                style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(56)),
                child: Text(_isSubmitting ? 'Analiz gonderiliyor...' : 'Analizi Al'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  List<Widget> _buildFabricRows() {
    return List<Widget>.generate(_fabricRows.length, (index) {
      final row = _fabricRows[index];
      return Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              flex: 5,
              child: TextField(
                controller: row.nameController,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Kumas tipi',
                  hintText: 'or. Viskon',
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              flex: 3,
              child: TextField(
                controller: row.percentageController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Oran %',
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              onPressed: _fabricRows.length == 1 ? null : () => _removeFabricRow(index),
              icon: const Icon(Icons.close),
              tooltip: 'Satiri kaldir',
            ),
          ],
        ),
      );
    });
  }

  void _addFabricRow() {
    setState(() {
      _fabricRows.add(_FabricInputRow());
    });
  }

  void _removeFabricRow(int index) {
    setState(() {
      final row = _fabricRows.removeAt(index);
      row.dispose();
    });
  }
}

class _FabricInputRow {
  _FabricInputRow({String name = '', String percentage = ''})
      : nameController = TextEditingController(
          text: name.isEmpty ? '' : FabricParser.displayLabel(name),
        ),
        percentageController = TextEditingController(text: percentage);

  final TextEditingController nameController;
  final TextEditingController percentageController;

  void dispose() {
    nameController.dispose();
    percentageController.dispose();
  }
}
