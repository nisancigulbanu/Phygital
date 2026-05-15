class FabricParser {
  static const Map<String, String> _keywordMap = {
    'pamuk': 'cotton',
    'cotton': 'cotton',
    'polyester': 'polyester',
    'polyesteri': 'polyester',
    'polyamid': 'polyamide',
    'polyami': 'polyamide',
    'poliamit': 'polyamide',
    'poliami': 'polyamide',
    'polyamide': 'polyamide',
    'naylon': 'polyamide',
    'nylon': 'polyamide',
    'akrilik': 'acrylic',
    'acrylic': 'acrylic',
    'elastan': 'elastane',
    'elastane': 'elastane',
    'spandex': 'elastane',
    'yun': 'wool',
    'yunlu': 'wool',
    'wool': 'wool',
    'viskon': 'viscose',
    'viskoz': 'viscose',
    'viscose': 'viscose',
    'organic cotton': 'organic cotton',
    'organik pamuk': 'organic cotton',
    'recycled polyester': 'recycled polyester',
    'geri donusturulmus polyester': 'recycled polyester',
    'merino wool': 'merino wool',
    'merinos yun': 'merino wool',
    'keten': 'linen',
    'linen': 'linen',
  };

  static const Map<String, String> _stemMap = {
    'pamuk': 'cotton',
    'cotton': 'cotton',
    'polyester': 'polyester',
    'polyamid': 'polyamide',
    'polyami': 'polyamide',
    'poliamit': 'polyamide',
    'poliami': 'polyamide',
    'polyamide': 'polyamide',
    'naylon': 'polyamide',
    'nylon': 'polyamide',
    'akrilik': 'acrylic',
    'acrylic': 'acrylic',
    'elastan': 'elastane',
    'elastane': 'elastane',
    'yun': 'wool',
    'wool': 'wool',
    'viskon': 'viscose',
    'viskoz': 'viscose',
    'viscose': 'viscose',
    'keten': 'linen',
    'linen': 'linen',
  };

  static const Map<String, String> _displayLabels = <String, String>{
    'cotton': 'Pamuk',
    'polyester': 'Polyester',
    'polyamide': 'Polyamid',
    'acrylic': 'Akrilik',
    'elastane': 'Elastan',
    'wool': 'Yun',
    'viscose': 'Viskon',
    'organic cotton': 'Organik Pamuk',
    'recycled polyester': 'Geri Donusturulmus Polyester',
    'merino wool': 'Merino Yun',
    'linen': 'Keten',
  };

  static final RegExp _leadingPercentPattern = RegExp(
    r'%\s*(\d{1,3})\s*([a-z]+(?:\s+[a-z]+){0,2})',
    caseSensitive: false,
  );
  static final RegExp _linePairPattern = RegExp(
    r'^([a-z]+(?:\s+[a-z]+){0,2})\s+(\d{1,3})$',
    caseSensitive: false,
  );
  static final RegExp _numberFirstPattern = RegExp(
    r'(\d{1,3})\s*%\s*([a-z]+(?:\s+[a-z]+){0,2})',
    caseSensitive: false,
  );

  static Map<String, int> parse(String text) {
    final results = <String, int>{};
    final normalizedText = _normalize(text);
    for (final match in _leadingPercentPattern.allMatches(normalizedText)) {
      _write(results, match.group(2), match.group(1));
    }
    for (final match in _numberFirstPattern.allMatches(normalizedText)) {
      _write(results, match.group(2), match.group(1));
    }

    final lines = normalizedText
        .split(RegExp(r'[\n,;]+'))
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty);

    for (final line in lines) {
      if (line.contains('%')) {
        continue;
      }
      final match = _linePairPattern.firstMatch(line);
      if (match != null) {
        _write(results, match.group(1), match.group(2));
      }
    }

    return {
      for (final entry in results.entries)
        if (entry.value > 0) entry.key: entry.value,
    };
  }

  static String normalizeFabricKey(String value) {
    final normalized = _normalize(value).trim();
    if (normalized.isEmpty) {
      return '';
    }
    final collapsed = normalized.replaceAll(RegExp(r'\s+'), ' ');
    if (_keywordMap.containsKey(collapsed)) {
      return _keywordMap[collapsed]!;
    }
    final words = collapsed.split(' ');
    for (var length = words.length; length > 0; length--) {
      final candidate = words.take(length).join(' ');
      final mapped = _keywordMap[candidate];
      if (mapped != null) {
        return mapped;
      }
    }
    final firstWord = words.isEmpty ? collapsed : words.first;
    for (final entry in _stemMap.entries) {
      if (firstWord.startsWith(entry.key)) {
        return entry.value;
      }
    }
    return collapsed;
  }

  static String displayLabel(String key) {
    return _displayLabels[key] ?? _toTitleCase(key.replaceAll('_', ' '));
  }

  static String _normalize(String value) {
    return value
        .toLowerCase()
        .replaceAll('Ã„Â±', 'i')
        .replaceAll('ÃƒÂ¶', 'o')
        .replaceAll('ÃƒÂ¼', 'u')
        .replaceAll('Ã…Å¸', 's')
        .replaceAll('Ã„Å¸', 'g')
        .replaceAll('ÃƒÂ§', 'c')
        .replaceAll('ı', 'i')
        .replaceAll('ö', 'o')
        .replaceAll('ü', 'u')
        .replaceAll('ş', 's')
        .replaceAll('ğ', 'g')
        .replaceAll('ç', 'c');
  }

  static void _write(Map<String, int> target, String? fabricWord, String? numberText) {
    if (fabricWord == null || numberText == null) {
      return;
    }
    final mapped = normalizeFabricKey(fabricWord);
    final number = int.tryParse(numberText);
    if (mapped.isNotEmpty && number != null) {
      target[mapped] = number;
    }
  }

  static String _toTitleCase(String value) {
    return value
        .split(' ')
        .where((part) => part.isNotEmpty)
        .map((part) => part[0].toUpperCase() + part.substring(1))
        .join(' ');
  }
}
