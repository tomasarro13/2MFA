import 'package:flutter/material.dart';

import '../controllers/accounts_controller.dart';
import 'scan_qr_page.dart';

class AddAccountPage extends StatefulWidget {
  const AddAccountPage({super.key, required this.controller});

  final AccountsController controller;

  @override
  State<AddAccountPage> createState() => _AddAccountPageState();
}

class _AddAccountPageState extends State<AddAccountPage> {
  final _formKey = GlobalKey<FormState>();
  final _issuer = TextEditingController(text: 'Lab2FA');
  final _label = TextEditingController();
  final _secret = TextEditingController();
  final _uri = TextEditingController();
  String? _error;

  @override
  void dispose() {
    for (final c in [_issuer, _label, _secret, _uri]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _run(Future<void> Function() action) async {
    try {
      await action();
      if (mounted) Navigator.pop(context);
    } on FormatException catch (e) {
      setState(() => _error = e.message);
    }
  }

  Future<void> _scan() async {
    final raw = await Navigator.push<String>(context, MaterialPageRoute(builder: (_) => const ScanQrPage()));
    if (raw != null) await _run(() => widget.controller.addFromUri(raw));
  }

  Future<void> _saveManual() async {
    if (_uri.text.trim().isNotEmpty) {
      return _run(() => widget.controller.addFromUri(_uri.text));
    }
    if (!_formKey.currentState!.validate()) return;
    await _run(() => widget.controller.addManually(
          issuer: _issuer.text,
          label: _label.text,
          secret: _secret.text,
        ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Agregar cuenta')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            FilledButton.icon(
              onPressed: _scan,
              icon: const Icon(Icons.qr_code_scanner),
              label: const Text('Escanear código QR'),
            ),
            const SizedBox(height: 24),
            Text('…o ingresa los datos manualmente', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 12),
            TextField(
              controller: _uri,
              decoration: const InputDecoration(
                labelText: 'URI otpauth:// (opcional)',
                hintText: 'otpauth://totp/Lab2FA:ana?secret=...',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            Form(
              key: _formKey,
              child: Column(
                children: [
                  TextFormField(
                    controller: _issuer,
                    decoration: const InputDecoration(labelText: 'Emisor', border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _label,
                    decoration: const InputDecoration(labelText: 'Cuenta / usuario', border: OutlineInputBorder()),
                    validator: (v) => (v == null || v.trim().isEmpty) ? 'Requerido' : null,
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _secret,
                    textCapitalization: TextCapitalization.characters,
                    decoration: const InputDecoration(labelText: 'Semilla Base32', border: OutlineInputBorder()),
                    validator: (v) => (v == null || v.trim().isEmpty) ? 'Requerido' : null,
                  ),
                ],
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            const SizedBox(height: 16),
            OutlinedButton(onPressed: _saveManual, child: const Text('Guardar')),
          ],
        ),
      ),
    );
  }
}
