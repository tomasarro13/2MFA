import '../entities/otp_account.dart';
import '../entities/otp_code.dart';
import '../services/totp_generator.dart';

typedef Clock = DateTime Function();

class GenerateCode {
  const GenerateCode(this._generator, this._clock);

  final OtpGenerator _generator;
  final Clock _clock;

  OtpCode call(OtpAccount account) => _generator.generate(account, _clock());
}
