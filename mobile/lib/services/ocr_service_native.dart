import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

class OcrService {
  OcrService() : _textRecognizer = TextRecognizer(script: TextRecognitionScript.latin);

  final TextRecognizer _textRecognizer;

  bool get supportsOnDeviceOcr {
    return defaultTargetPlatform == TargetPlatform.android ||
        defaultTargetPlatform == TargetPlatform.iOS;
  }

  Future<String> extractText(String imagePath) async {
    if (!supportsOnDeviceOcr) {
      throw UnsupportedError('on_device_ocr_not_supported');
    }
    final inputImage = InputImage.fromFile(File(imagePath));
    final recognizedText = await _textRecognizer.processImage(inputImage);
    return recognizedText.text;
  }

  bool looksUseful(String text) {
    final normalized = text.trim();
    if (normalized.length < 8) {
      return false;
    }
    final percentageMatches = RegExp(r'\d{1,3}\s*%|%\s*\d{1,3}').allMatches(normalized).length;
    return percentageMatches > 0 || normalized.split(RegExp(r'\s+')).length >= 4;
  }

  void dispose() {
    _textRecognizer.close();
  }
}
