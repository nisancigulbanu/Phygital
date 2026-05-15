class OcrService {
  bool get supportsOnDeviceOcr => false;

  Future<String> extractText(String imagePath) {
    throw UnsupportedError('on_device_ocr_not_supported');
  }

  bool looksUseful(String text) {
    final normalized = text.trim();
    if (normalized.length < 8) {
      return false;
    }
    final percentageMatches = RegExp(r'\d{1,3}\s*%|%\s*\d{1,3}').allMatches(normalized).length;
    return percentageMatches > 0 || normalized.split(RegExp(r'\s+')).length >= 4;
  }

  void dispose() {}
}
