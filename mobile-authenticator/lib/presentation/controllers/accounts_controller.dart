import 'package:flutter/foundation.dart';

import '../../domain/entities/otp_account.dart';
import '../../domain/usecases/account_usecases.dart';

class AccountsController extends ChangeNotifier {
  AccountsController(this._getAccounts, this._addFromUri, this._addManually, this._deleteAccount);

  final GetAccounts _getAccounts;
  final AddAccountFromUri _addFromUri;
  final AddAccountManually _addManually;
  final DeleteAccount _deleteAccount;

  List<OtpAccount> _accounts = const [];
  bool _loading = true;

  List<OtpAccount> get accounts => _accounts;
  bool get loading => _loading;

  Future<void> load() async {
    _accounts = await _getAccounts();
    _loading = false;
    notifyListeners();
  }

  Future<void> addFromUri(String uri) async {
    await _addFromUri(uri);
    await load();
  }

  Future<void> addManually({required String issuer, required String label, required String secret}) async {
    await _addManually(issuer: issuer, label: label, secret: secret);
    await load();
  }

  Future<void> delete(String id) async {
    await _deleteAccount(id);
    await load();
  }
}
