/// Datos extraídos de una URI otpauth://totp/Issuer:cuenta?secret=...
class OtpAuthData {
  const OtpAuthData({
    required this.issuer,
    required this.label,
    required this.secret,
    required this.digits,
    required this.period,
  });

  final String issuer;
  final String label;
  final String secret;
  final int digits;
  final int period;
}

class OtpAuthUriParser {
  const OtpAuthUriParser();

  OtpAuthData parse(String raw) {
    final uri = Uri.tryParse(raw.trim());
    if (uri == null || uri.scheme != 'otpauth' || uri.host != 'totp') {
      throw const FormatException('No es una URI otpauth://totp/ válida');
    }
    final secret = uri.queryParameters['secret'];
    if (secret == null || secret.isEmpty) {
      throw const FormatException('La URI no contiene el parámetro secret');
    }
    final algorithm = (uri.queryParameters['algorithm'] ?? 'SHA1').toUpperCase();
    if (algorithm != 'SHA1') {
      throw FormatException('Algoritmo no soportado: $algorithm');
    }

    final path = Uri.decodeComponent(uri.path.replaceFirst('/', ''));
    final parts = path.split(':');
    final label = parts.length > 1 ? parts.sublist(1).join(':').trim() : path.trim();
    final issuer = uri.queryParameters['issuer'] ?? (parts.length > 1 ? parts.first.trim() : '');

    return OtpAuthData(
      issuer: issuer,
      label: label,
      secret: secret,
      digits: int.tryParse(uri.queryParameters['digits'] ?? '') ?? 6,
      period: int.tryParse(uri.queryParameters['period'] ?? '') ?? 30,
    );
  }
}
