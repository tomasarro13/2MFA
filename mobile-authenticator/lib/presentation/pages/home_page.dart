import 'package:flutter/material.dart';

import '../../domain/entities/otp_account.dart';
import '../../domain/usecases/generate_code.dart';
import '../controllers/accounts_controller.dart';
import '../widgets/account_code_card.dart';
import 'add_account_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key, required this.controller, required this.generateCode});

  final AccountsController controller;
  final GenerateCode generateCode;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
    widget.controller.load();
  }

  Future<void> _confirmDelete(OtpAccount account) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar cuenta'),
        content: Text('¿Eliminar "${account.displayName}"? No podrás generar más códigos para ella.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Eliminar')),
        ],
      ),
    );
    if (ok == true) await widget.controller.delete(account.id);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mi Authenticator')),
      body: ListenableBuilder(
        listenable: widget.controller,
        builder: (context, _) {
          if (widget.controller.loading) {
            return const Center(child: CircularProgressIndicator());
          }
          final accounts = widget.controller.accounts;
          if (accounts.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Text('Aún no hay cuentas.\nEscanea el QR del backend o pega la semilla Base32.',
                    textAlign: TextAlign.center),
              ),
            );
          }
          return ListView(
            padding: const EdgeInsets.only(top: 8, bottom: 96),
            children: [
              for (final account in accounts)
                AccountCodeCard(
                  key: ValueKey(account.id),
                  account: account,
                  generateCode: widget.generateCode,
                  onDelete: () => _confirmDelete(account),
                ),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => AddAccountPage(controller: widget.controller)),
        ),
        icon: const Icon(Icons.add),
        label: const Text('Agregar'),
      ),
    );
  }
}
