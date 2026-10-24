import '../entities/otp_account.dart';
import '../repositories/account_repository.dart';
import '../services/base32_decoder.dart';
import '../services/otpauth_uri_parser.dart';

typedef IdGenerator = String Function();

class GetAccounts {
  const GetAccounts(this._repository);

  final AccountRepository _repository;

  Future<List<OtpAccount>> call() => _repository.getAll();
}

class AddAccountManually {
  const AddAccountManually(this._repository, this._newId, [this._base32 = const Base32Decoder()]);

  final AccountRepository _repository;
  final IdGenerator _newId;
  final Base32Decoder _base32;

  Future<OtpAccount> call({required String issuer, required String label, required String secret}) async {
    final normalized = secret.replaceAll(RegExp(r'\s'), '').toUpperCase();
    _base32.decode(normalized); // lanza FormatException si no es Base32
    final account = OtpAccount(id: _newId(), issuer: issuer.trim(), label: label.trim(), secret: normalized);
    await _repository.save(account);
    return account;
  }
}

class AddAccountFromUri {
  const AddAccountFromUri(this._repository, this._newId,
      [this._parser = const OtpAuthUriParser(), this._base32 = const Base32Decoder()]);

  final AccountRepository _repository;
  final IdGenerator _newId;
  final OtpAuthUriParser _parser;
  final Base32Decoder _base32;

  Future<OtpAccount> call(String uri) async {
    final data = _parser.parse(uri);
    _base32.decode(data.secret);
    final account = OtpAccount(
      id: _newId(),
      issuer: data.issuer,
      label: data.label,
      secret: data.secret.toUpperCase(),
      digits: data.digits,
      period: data.period,
    );
    await _repository.save(account);
    return account;
  }
}

class DeleteAccount {
  const DeleteAccount(this._repository);

  final AccountRepository _repository;

  Future<void> call(String id) => _repository.delete(id);
}
