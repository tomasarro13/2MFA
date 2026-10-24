import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_authenticator/domain/services/base32_decoder.dart';
import 'package:mobile_authenticator/domain/services/otpauth_uri_parser.dart';

void main() {
  const decoder = Base32Decoder();

  test('decodifica Base32 ignorando mayúsculas, espacios y padding', () {
    expect(String.fromCharCodes(decoder.decode('MZXW6YTBOI======')), 'foobar');
    expect(String.fromCharCodes(decoder.decode('mzxw 6ytb oi')), 'foobar');
  });

  test('rechaza caracteres fuera del alfabeto', () {
    expect(() => decoder.decode('ABC1'), throwsFormatException);
  });

  test('extrae secret, issuer y cuenta de la URI otpauth del backend', () {
    final data = const OtpAuthUriParser().parse(
        'otpauth://totp/Lab2FA%3Aana?secret=JBSWY3DPEHPK3PXP&issuer=Lab2FA&algorithm=SHA1&digits=6&period=30');
    expect(data.secret, 'JBSWY3DPEHPK3PXP');
    expect(data.issuer, 'Lab2FA');
    expect(data.label, 'ana');
    expect(data.digits, 6);
    expect(data.period, 30);
  });

  test('rechaza URIs que no son otpauth://totp', () {
    expect(() => const OtpAuthUriParser().parse('https://example.com'), throwsFormatException);
  });
}
