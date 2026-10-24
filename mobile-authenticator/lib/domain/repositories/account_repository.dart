import '../entities/otp_account.dart';

abstract interface class AccountRepository {
  Future<List<OtpAccount>> getAll();

  Future<void> save(OtpAccount account);

  Future<void> delete(String id);
}
