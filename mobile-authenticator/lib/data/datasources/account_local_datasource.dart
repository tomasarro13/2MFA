import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class AccountLocalDataSource {
  Future<List<Map<String, dynamic>>> readAll();

  Future<void> writeAll(List<Map<String, dynamic>> accounts);
}

/// Guarda las semillas en Keychain (iOS) / Keystore (Android). Funciona sin red.
class SecureStorageAccountDataSource implements AccountLocalDataSource {
  SecureStorageAccountDataSource([FlutterSecureStorage? storage])
      : _storage = storage ?? const FlutterSecureStorage();

  static const _key = 'otp_accounts';
  final FlutterSecureStorage _storage;

  @override
  Future<List<Map<String, dynamic>>> readAll() async {
    final raw = await _storage.read(key: _key);
    if (raw == null || raw.isEmpty) return [];
    return (jsonDecode(raw) as List).cast<Map<String, dynamic>>();
  }

  @override
  Future<void> writeAll(List<Map<String, dynamic>> accounts) =>
      _storage.write(key: _key, value: jsonEncode(accounts));
}

/// Implementación en memoria para pruebas.
class InMemoryAccountDataSource implements AccountLocalDataSource {
  List<Map<String, dynamic>> _data = [];

  @override
  Future<List<Map<String, dynamic>>> readAll() async => List.of(_data);

  @override
  Future<void> writeAll(List<Map<String, dynamic>> accounts) async => _data = List.of(accounts);
}
