/// Cuenta TOTP almacenada en el dispositivo.
class OtpAccount {
  const OtpAccount({
    required this.id,
    required this.issuer,
    required this.label,
    required this.secret,
    this.digits = 6,
    this.period = 30,
  });

  final String id;
  final String issuer;
  final String label;

  /// Semilla en Base32 tal como la entrega el backend.
  final String secret;
  final int digits;
  final int period;

  String get displayName => issuer.isEmpty ? label : '$issuer · $label';
}
