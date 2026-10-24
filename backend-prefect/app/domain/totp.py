"""Algoritmo TOTP (RFC 6238 / RFC 4226) implementado desde cero.

Funciones puras: solo dependen de primitivas estándar (hmac, hashlib, struct, base64).
"""
import base64
import hashlib
import hmac
import struct
from urllib.parse import quote

STEP_SECONDS = 30
DIGITS = 6


def b32_decode(secret: str) -> bytes:
    cleaned = secret.replace(" ", "").upper()
    cleaned += "=" * (-len(cleaned) % 8)
    return base64.b32decode(cleaned)


def counter_at(unix_time: float) -> int:
    """C = floor(UnixTime / 30)."""
    return int(unix_time // STEP_SECONDS)


def hotp(key: bytes, counter: int, digits: int = DIGITS) -> str:
    msg = struct.pack(">Q", counter)  # 8 bytes, big-endian
    digest = hmac.new(key, msg, hashlib.sha1).digest()  # 20 bytes
    offset = digest[19] & 0x0F
    binary = (
        ((digest[offset] & 0x7F) << 24)
        | (digest[offset + 1] << 16)
        | (digest[offset + 2] << 8)
        | digest[offset + 3]
    )
    return str(binary % (10**digits)).zfill(digits)


def totp(secret_b32: str, unix_time: float) -> str:
    return hotp(b32_decode(secret_b32), counter_at(unix_time))


def provisioning_uri(secret_b32: str, account: str, issuer: str) -> str:
    label = quote(f"{issuer}:{account}")
    return (
        f"otpauth://totp/{label}?secret={secret_b32}&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={DIGITS}&period={STEP_SECONDS}"
    )
