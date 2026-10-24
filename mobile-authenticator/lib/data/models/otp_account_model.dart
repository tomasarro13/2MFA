import '../../domain/entities/otp_account.dart';

class OtpAccountModel {
  const OtpAccountModel._();

  static Map<String, dynamic> toJson(OtpAccount a) => {
        'id': a.id,
        'issuer': a.issuer,
        'label': a.label,
        'secret': a.secret,
        'digits': a.digits,
        'period': a.period,
      };

  static OtpAccount fromJson(Map<String, dynamic> json) => OtpAccount(
        id: json['id'] as String,
        issuer: json['issuer'] as String? ?? '',
        label: json['label'] as String? ?? '',
        secret: json['secret'] as String,
        digits: json['digits'] as int? ?? 6,
        period: json['period'] as int? ?? 30,
      );
}
