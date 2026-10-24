import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_authenticator/data/crypto/crypto_hmac_sha1.dart';
import 'package:mobile_authenticator/domain/entities/otp_account.dart';
import 'package:mobile_authenticator/domain/services/base32_decoder.dart';
import 'package:mobile_authenticator/domain/services/totp_generator.dart';

// RFC 6238, Apéndice B (SHA1). Secreto ASCII "12345678901234567890".
const rfcSecret = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ';
const rfcVectors = {
  59: '94287082',
  1111111109: '07081804',
  1111111111: '14050471',
  1234567890: '89005924',
  2000000000: '69279037',
  20000000000: '65353130',
};

DateTime at(int seconds) => DateTime.fromMillisecondsSinceEpoch(seconds * 1000, isUtc: true);

void main() {
  const generator = TotpGenerator(CryptoHmacSha1());

  test('cumple los vectores de prueba del RFC 6238 (8 dígitos)', () {
    final key = const Base32Decoder().decode(rfcSecret);
    rfcVectors.forEach((t, expected) {
      expect(generator.hotp(key, t ~/ 30, digits: 8), expected, reason: 't=$t');
    });
  });

  test('genera 6 dígitos con contador y segundos restantes', () {
    const account = OtpAccount(id: '1', issuer: 'RFC', label: 'test', secret: rfcSecret);
    final code = generator.generate(account, at(59));
    expect(code.value, '287082');
    expect(code.counter, 1);
    expect(code.secondsRemaining, 1);
  });

  test('coincide con el backend Python para el mismo secreto e instante', () {
    const account = OtpAccount(id: '1', issuer: 'Lab2FA', label: 'ana', secret: 'JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP');
    expect(generator.generate(account, at(1792857079)).value, '652723');
  });
}
