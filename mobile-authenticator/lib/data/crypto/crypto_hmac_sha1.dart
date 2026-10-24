import 'package:crypto/crypto.dart';

import '../../domain/services/mac_algorithm.dart';

/// Adaptador de package:crypto (solo HMAC-SHA1, no calcula TOTP).
class CryptoHmacSha1 implements MacAlgorithm {
  const CryptoHmacSha1();

  @override
  List<int> sign(List<int> key, List<int> message) => Hmac(sha1, key).convert(message).bytes;
}
