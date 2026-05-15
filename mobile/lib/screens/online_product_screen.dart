import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/analysis_draft.dart';
import '../models/product_lookup_result.dart';
import '../services/api_service.dart';
import '../services/ocr_service.dart';
import 'review_screen.dart';

class OnlineProductScreen extends StatefulWidget {
  const OnlineProductScreen({super.key});

  @override
  State<OnlineProductScreen> createState() => _OnlineProductScreenState();
}

class _OnlineProductScreenState extends State<OnlineProductScreen> {
  final _apiService = ApiService();
  final _ocrService = OcrService();
  final _picker = ImagePicker();
  final _urlController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _urlController.dispose();
    _ocrService.dispose();
    super.dispose();
  }

  Future<void> _analyzeLink() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      setState(() => _error = 'Lutfen bir urun linki gir.');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final ProductLookupResult result = await _apiService.extractProduct(productUrl: url);
      if (!mounted) {
        return;
      }

      setState(() => _isLoading = false);
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ReviewScreen(
            initialDraft: result.toDraft(sourceUrl: url),
          ),
        ),
      );
    } on ApiException catch (error) {
      setState(() {
        _isLoading = false;
        _error = error.message;
      });
    } catch (_) {
      setState(() {
        _isLoading = false;
        _error = 'Linkten urun bilgisi cekilemedi. Sayfa dinamik olabilir; ekran goruntusu ile devam edebilirsin.';
      });
    }
  }

  Future<void> _pickScreenshot() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final image = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 90);
      if (image == null) {
        setState(() => _isLoading = false);
        return;
      }

      final imageBytes = await image.readAsBytes();
      AnalysisDraft draft;
      try {
        if (_ocrService.supportsOnDeviceOcr) {
          final extractedText = await _ocrService.extractText(image.path);
          if (_ocrService.looksUseful(extractedText)) {
            draft = draftFromText(extractedText, imagePath: image.path);
          } else {
            draft = await _apiService.scanLabelImage(imageBytes: imageBytes, imagePath: image.path);
          }
        } else {
          draft = await _apiService.scanLabelImage(imageBytes: imageBytes, imagePath: image.path);
        }
      } on ApiException {
        draft = draftFromText('', imagePath: image.path);
      }
      draft.notes = 'Bu taslak ekran goruntusunden OCR ile cikarildi. Marka, fiyat ve kumas oranlarini kontrol et.';

      if (!mounted) {
        return;
      }

      setState(() => _isLoading = false);
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ReviewScreen(initialDraft: draft),
        ),
      );
    } catch (_) {
      setState(() {
        _isLoading = false;
        _error = 'Ekran goruntusu okunamadi. Daha net bir goruntu dene.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Online Urun Analizi')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text('Urun linki ekle', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
                  SizedBox(height: 12),
                  Text(
                    'Bir urun sayfasinin linkini ver. Sistem urun adini, fiyatini ve varsa kumas bilgisini bulup analize hazirlar.',
                    style: TextStyle(height: 1.5),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _urlController,
            keyboardType: TextInputType.url,
            decoration: const InputDecoration(
              labelText: 'Urun linki',
              hintText: 'https://...',
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: _isLoading ? null : _analyzeLink,
              child: Text(_isLoading ? 'Link analiz ediliyor...' : 'Linkten Urun Bul'),
            ),
          ),
          const SizedBox(height: 24),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Alternatif: ekran goruntusu ekle', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 12),
                  const Text(
                    'Urun sayfasinin ekran goruntusunu galeriden secersen OCR ile veri cikarir, sonra sen son kontrolu yaparsin.',
                    style: TextStyle(height: 1.5),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: _isLoading ? null : _pickScreenshot,
                      icon: const Icon(Icons.image_search_outlined),
                      label: const Text('Ekran Goruntusu Sec'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.redAccent)),
          ],
        ],
      ),
    );
  }
}
