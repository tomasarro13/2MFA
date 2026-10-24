import base64
import secrets

from ...application.ports import SecretGenerator


class CryptoSecretGenerator(SecretGenerator):
    def totp_secret(self) -> str:
        # 160 bits, el tamaño recomendado para HMAC-SHA1. Base32 sin padding.
        return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")

    def backup_codes(self, count: int) -> list[str]:
        return [secrets.token_hex(4).upper() for _ in range(count)]
