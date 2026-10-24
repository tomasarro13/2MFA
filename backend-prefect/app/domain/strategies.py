"""Strategy Pattern para el segundo factor.

Las estrategias no persisten nada (SRP): devuelven un resultado y la capa de
aplicación decide qué hacer con él. Sus dependencias (reloj, hash) se inyectan
como funciones (DIP), lo que las hace deterministas en pruebas.
"""
import hmac
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from . import totp
from .entities import User


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    detail: str
    window_offset: int | None = None        # TOTP: -1, 0 ó +1
    consumed_backup_hash: str | None = None  # Backup: hash a invalidar


class SecondFactorStrategy(ABC):
    name: str

    @abstractmethod
    def verify(self, user: User, code: str) -> VerificationResult: ...


class TOTPStrategy(SecondFactorStrategy):
    name = "totp"
    WINDOWS = (-1, 0, 1)  # C-1, C, C+1

    def __init__(self, clock: Callable[[], float]):
        self._clock = clock

    def verify(self, user: User, code: str) -> VerificationResult:
        if not user.totp_secret:
            return VerificationResult(False, "El usuario no tiene secreto TOTP")
        key = totp.b32_decode(user.totp_secret)
        c = totp.counter_at(self._clock())
        for offset in self.WINDOWS:
            if hmac.compare_digest(totp.hotp(key, c + offset), code):
                label = "C" if offset == 0 else f"C{offset:+d}"
                return VerificationResult(True, f"Match en ventana {label} (contador {c + offset})", offset)
        return VerificationResult(False, f"El código no coincide en las ventanas C-1, C, C+1 (C={c})")


class BackupCodeStrategy(SecondFactorStrategy):
    name = "backup"

    def __init__(self, hash_code: Callable[[str], str]):
        self._hash_code = hash_code

    def verify(self, user: User, code: str) -> VerificationResult:
        hashed = self._hash_code(code)
        if hashed not in user.backup_code_hashes:
            return VerificationResult(False, "Código de respaldo inválido o ya utilizado")
        remaining = len(user.backup_code_hashes) - 1
        return VerificationResult(True, f"Código de respaldo aceptado ({remaining} restantes)",
                                  consumed_backup_hash=hashed)
