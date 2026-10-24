/// Código generado para un instante concreto.
class OtpCode {
  const OtpCode({
    required this.value,
    required this.counter,
    required this.secondsRemaining,
    required this.period,
  });

  final String value;

  /// C = floor(UnixTime / period)
  final int counter;
  final int secondsRemaining;
  final int period;

  double get progress => secondsRemaining / period;
}
