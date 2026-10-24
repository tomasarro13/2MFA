import 'dart:typed_data';

import '../entities/otp_account.dart';
import '../entities/otp_code.dart';
import 'base32_decoder.dart';
import 'mac_algorithm.dart';

abstract interface class OtpGenerator {
  OtpCode generate(OtpAccount account, DateTime now);
}

/// TOTP según RFC 6238, paso a paso como lo pide la guía del laboratorio.
class TotpGenerator implements OtpGenerator {
  const TotpGenerator(this._hmacSha1, [this._base32 = const Base32Decoder()]);

  final MacAlgorithm _hmacSha1;
  final Base32Decoder _base32;

  @override
  OtpCode generate(OtpAccount account, DateTime now) {
    final unixSeconds = now.millisecondsSinceEpoch ~/ 1000;
    final counter = unixSeconds ~/ account.period;
    return OtpCode(
      value: hotp(_base32.decode(account.secret), counter, digits: account.digits),
      counter: counter,
      secondsRemaining: account.period - (unixSeconds % account.period),
      period: account.period,
    );
  }

  String hotp(List<int> key, int counter, {int digits = 6}) {
    // 1. Contador como entero de 8 bytes big-endian.
    final message = ByteData(8)
      ..setUint32(0, (counter >> 32) & 0xFFFFFFFF)
      ..setUint32(4, counter & 0xFFFFFFFF);

    // 2. HMAC-SHA1(K, C) -> 20 bytes.
    final hash = _hmacSha1.sign(key, message.buffer.asUint8List());

    // 3. Truncamiento dinámico.
    final offset = hash[19] & 0x0f;
    final binary = ((hash[offset] & 0x7f) << 24) |
        (hash[offset + 1] << 16) |
        (hash[offset + 2] << 8) |
        hash[offset + 3];

    // 4. Módulo 10^digits y relleno con ceros.
    var modulus = 1;
    for (var i = 0; i < digits; i++) {
      modulus *= 10;
    }
    return (binary % modulus).toString().padLeft(digits, '0');
  }
}
