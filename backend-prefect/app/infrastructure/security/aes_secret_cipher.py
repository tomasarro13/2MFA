import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ...application.ports import SecretCipher


class AesGcmSecretCipher(SecretCipher):
    """AES-256-GCM: confidencialidad + integridad. Formato: base64(nonce || ciphertext+tag)."""

    NONCE_SIZE = 12

    def __init__(self, key_b64: str):
        key = base64.urlsafe_b64decode(key_b64)
        if len(key) != 32:
            raise ValueError("TOTP_ENCRYPTION_KEY debe ser de 32 bytes en base64")
        self._aes = AESGCM(key)

    def encrypt(self, plaintext: str, context: str) -> str:
        nonce = os.urandom(self.NONCE_SIZE)
        ciphertext = self._aes.encrypt(nonce, plaintext.encode(), context.encode())
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def decrypt(self, token: str, context: str) -> str:
        raw = base64.urlsafe_b64decode(token)
        nonce, ciphertext = raw[:self.NONCE_SIZE], raw[self.NONCE_SIZE:]
        return self._aes.decrypt(nonce, ciphertext, context.encode()).decode()
