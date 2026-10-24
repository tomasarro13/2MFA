import '../../domain/entities/otp_account.dart';
import '../../domain/repositories/account_repository.dart';
import '../datasources/account_local_datasource.dart';
import '../models/otp_account_model.dart';

class AccountRepositoryImpl implements AccountRepository {
  const AccountRepositoryImpl(this._dataSource);

  final AccountLocalDataSource _dataSource;

  @override
  Future<List<OtpAccount>> getAll() async =>
      (await _dataSource.readAll()).map(OtpAccountModel.fromJson).toList();

  @override
  Future<void> save(OtpAccount account) async {
    final accounts = await getAll()
      ..removeWhere((a) => a.id == account.id)
      ..add(account);
    await _dataSource.writeAll(accounts.map(OtpAccountModel.toJson).toList());
  }

  @override
  Future<void> delete(String id) async {
    final accounts = await getAll()
      ..removeWhere((a) => a.id == id);
    await _dataSource.writeAll(accounts.map(OtpAccountModel.toJson).toList());
  }
}
