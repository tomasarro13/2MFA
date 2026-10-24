import 'dart:typed_data';

/// Decodificador Base32 (RFC 4648) implementado a mano.
class Base32Decoder {
  const Base32Decoder();

  static const _alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

  Uint8List decode(String input) {
    final cleaned = input.replaceAll(RegExp(r'[\s=-]'), '').toUpperCase();
    if (cleaned.isEmpty) {
      throw const FormatException('El secreto está vacío');
    }

    final output = BytesBuilder();
    var buffer = 0;
    var bitsInBuffer = 0;

    for (final char in cleaned.split('')) {
      final value = _alphabet.indexOf(char);
      if (value < 0) {
        throw FormatException('Carácter Base32 inválido: "$char"');
      }
      // Cada carácter aporta 5 bits; cuando hay 8 o más se emite un byte.
      buffer = (buffer << 5) | value;
      bitsInBuffer += 5;
      if (bitsInBuffer >= 8) {
        bitsInBuffer -= 8;
        output.addByte((buffer >> bitsInBuffer) & 0xFF);
      }
    }
    return output.toBytes();
  }

  bool isValid(String input) {
    try {
      decode(input);
      return true;
    } on FormatException {
      return false;
    }
  }
}
