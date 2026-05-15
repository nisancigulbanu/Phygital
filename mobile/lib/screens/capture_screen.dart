import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/analysis_draft.dart';
import '../services/api_service.dart';
import '../services/ocr_service.dart';
import 'review_screen.dart';

class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key});

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  final ImagePicker _picker = ImagePicker();
  final OcrService _ocrService = OcrService();
  final ApiService _apiService = ApiService();
  bool _isBusy = false;
  String? _error;
  Uint8List? _selectedImageBytes;

  @override
  void dispose() {
    _ocrService.dispose();
    super.dispose();
  }

  Future<void> _pick(ImageSource source) async {
    setState(() {
      _isBusy = true;
      _error = null;
    });
    try {
      final image = await _picker.pickImage(source: source, imageQuality: 85);
      if (image == null) {
        setState(() => _isBusy = false);
        return;
      }

      final imageBytes = await image.readAsBytes();
      final draft = await _buildDraft(image, imageBytes);
      if (!mounted) {
        return;
      }

      setState(() {
        _selectedImageBytes = imageBytes;
        _isBusy = false;
      });
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ReviewScreen(initialDraft: draft),
        ),
      );
    } catch (_) {
      setState(() {
        _error = 'Etiket okunurken bir sorun oldu. Daha net bir fotograf deneyin veya oranlari elle girin.';
        _isBusy = false;
      });
    }
  }

  Future<AnalysisDraft> _buildDraft(XFile image, Uint8List imageBytes) async {
    if (_ocrService.supportsOnDeviceOcr) {
      try {
        final extractedText = await _ocrService.extractText(image.path);
        if (_ocrService.looksUseful(extractedText)) {
          return draftFromText(extractedText, imagePath: image.path);
        }
      } catch (_) {
        // Continue with backend OCR fallback.
      }
    }

    try {
      return await _apiService.scanLabelImage(
        imageBytes: imageBytes,
        imagePath: image.path,
      );
    } on ApiException {
      final draft = draftFromText('', imagePath: image.path);
      draft.notes =
          'OCR otomatik olarak guvenilir sonuc veremedi. Kumas adlarini ve oranlarini elle doldurabilirsiniz.';
      return draft;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Etiketi Tara')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Expanded(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Kumas etiketini kadraja alin',
                        style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Yuzdelerin net gorunmesi OCR basarisini ciddi bicimde artirir. Isik duzgun ve yazilar tam gorunur olsun.',
                        style: TextStyle(height: 1.5),
                      ),
                      const SizedBox(height: 20),
                      Expanded(
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            color: const Color(0xFFEDF2EE),
                            borderRadius: BorderRadius.circular(24),
                          ),
                          child: Center(
                            child: _selectedImageBytes == null
                                ? const Icon(Icons.checkroom_outlined, size: 72, color: Color(0xFF184E42))
                                : ClipRRect(
                                    borderRadius: BorderRadius.circular(18),
                                    child: Image.memory(
                                      _selectedImageBytes!,
                                      fit: BoxFit.cover,
                                      width: double.infinity,
                                    ),
                                  ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(_error!, style: const TextStyle(color: Colors.redAccent)),
            ],
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _isBusy ? null : () => _pick(ImageSource.gallery),
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Galeriden Sec'),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _isBusy ? null : () => _pick(ImageSource.camera),
                icon: _isBusy
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.camera_alt_outlined),
                label: Text(_isBusy ? 'Etiket okunuyor...' : 'Kamera ile Tara'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
