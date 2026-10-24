import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_authenticator/data/datasources/account_local_datasource.dart';
import 'package:mobile_authenticator/data/repositories/account_repository_impl.dart';
import 'package:mobile_authenticator/domain/usecases/account_usecases.dart';

void main() {
  late AccountRepositoryImpl repo;
  var seq = 0;
  String newId() => '${seq++}';

  setUp(() => repo = AccountRepositoryImpl(InMemoryAccountDataSource()));

  test('agrega desde URI, lista y elimina', () async {
    final account = await AddAccountFromUri(repo, newId)('otpauth://totp/Lab2FA:ana?secret=jbswy3dpehpk3pxp');
    expect(account.secret, 'JBSWY3DPEHPK3PXP');
    expect(await GetAccounts(repo)(), hasLength(1));
    await DeleteAccount(repo)(account.id);
    expect(await GetAccounts(repo)(), isEmpty);
  });

  test('alta manual valida la semilla Base32', () async {
    expect(() => AddAccountManually(repo, newId)(issuer: 'x', label: 'y', secret: 'NO-VALIDA-1'),
        throwsFormatException);
  });
}
