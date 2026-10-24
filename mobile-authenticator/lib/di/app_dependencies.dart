import '../data/crypto/crypto_hmac_sha1.dart';
import '../data/datasources/account_local_datasource.dart';
import '../data/repositories/account_repository_impl.dart';
import '../domain/services/totp_generator.dart';
import '../domain/usecases/account_usecases.dart';
import '../domain/usecases/generate_code.dart';
import '../presentation/controllers/accounts_controller.dart';

/// Composition Root: único lugar que conoce las implementaciones concretas.
class AppDependencies {
  AppDependencies._(this.accountsController, this.generateCode);

  factory AppDependencies.create({AccountLocalDataSource? dataSource}) {
    final repository = AccountRepositoryImpl(dataSource ?? SecureStorageAccountDataSource());
    String newId() => DateTime.now().microsecondsSinceEpoch.toString();

    return AppDependencies._(
      AccountsController(
        GetAccounts(repository),
        AddAccountFromUri(repository, newId),
        AddAccountManually(repository, newId),
        DeleteAccount(repository),
      ),
      GenerateCode(const TotpGenerator(CryptoHmacSha1()), DateTime.now),
    );
  }

  final AccountsController accountsController;
  final GenerateCode generateCode;
}
