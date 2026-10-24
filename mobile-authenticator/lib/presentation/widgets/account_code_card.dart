import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../domain/entities/otp_account.dart';
import '../../domain/entities/otp_code.dart';
import '../../domain/usecases/generate_code.dart';

class AccountCodeCard extends StatefulWidget {
  const AccountCodeCard({super.key, required this.account, required this.generateCode, required this.onDelete});

  final OtpAccount account;
  final GenerateCode generateCode;
  final VoidCallback onDelete;

  @override
  State<AccountCodeCard> createState() => _AccountCodeCardState();
}

class _AccountCodeCardState extends State<AccountCodeCard> {
  late OtpCode _code;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _refresh();
    // Se recalcula cada segundo: el contador regresivo baja y, al llegar a 0,
    // cambia C y por lo tanto el código. No requiere conexión.
    _timer = Timer.periodic(const Duration(seconds: 1), (_) => setState(_refresh));
  }

  void _refresh() => _code = widget.generateCode(widget.account);

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String get _formatted {
    final v = _code.value;
    final half = v.length ~/ 2;
    return '${v.substring(0, half)} ${v.substring(half)}';
  }

  Future<void> _copy() async {
    await Clipboard.setData(ClipboardData(text: _code.value));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Código copiado')));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final expiring = _code.secondsRemaining <= 5;
    final color = expiring ? theme.colorScheme.error : theme.colorScheme.primary;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: _copy,
        onLongPress: widget.onDelete,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(widget.account.displayName, style: theme.textTheme.titleMedium),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      _formatted,
                      style: theme.textTheme.displayMedium?.copyWith(
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.w600,
                        letterSpacing: 4,
                        color: color,
                      ),
                    ),
                  ),
                  SizedBox(
                    width: 44,
                    height: 44,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        CircularProgressIndicator(value: _code.progress, color: color, strokeWidth: 4),
                        Text('${_code.secondsRemaining}', style: theme.textTheme.labelLarge),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              LinearProgressIndicator(value: _code.progress, color: color),
              const SizedBox(height: 6),
              Text('C = ${_code.counter} · toca para copiar, mantén para borrar',
                  style: theme.textTheme.bodySmall),
            ],
          ),
        ),
      ),
    );
  }
}
