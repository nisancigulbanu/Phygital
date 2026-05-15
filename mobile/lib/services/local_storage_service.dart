import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class LocalStorageService {
  LocalStorageService() : _storage = const FlutterSecureStorage();

  final FlutterSecureStorage _storage;
  static const _userIdKey = 'phygital_user_id';

  Future<String> getOrCreateUserId() async {
    final existing = await _storage.read(key: _userIdKey);
    if (existing != null && existing.isNotEmpty) {
      return existing;
    }

    final generated = 'user_${DateTime.now().millisecondsSinceEpoch}';
    await _storage.write(key: _userIdKey, value: generated);
    return generated;
  }
}
