"""Puertos (interfaces) que la capa de aplicación necesita del mundo exterior.

Interface Segregation: cada puerto expone solo lo que un caso de uso consume.
Dependency Inversion: la infraestructura implementa estos contratos.
"""
from abc import ABC, abstractmethod

from ..domain.entities import User
from .dto import TokenClaims, TokenScope


class UserRepository(ABC):
    @abstractmethod
    def add(self, username: str, password_hash: str) -> User: ...

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def save(self, user: User) -> None: ...


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool: ...


class BackupCodeHasher(ABC):
    @abstractmethod
    def hash(self, code: str) -> str: ...


class SecretCipher(ABC):
    """Cifrado reversible para secretos que el servidor necesita en claro (p. ej. TOTP)."""

    @abstractmethod
    def encrypt(self, plaintext: str, context: str) -> str: ...

    @abstractmethod
    def decrypt(self, token: str, context: str) -> str: ...


class TokenService(ABC):
    @abstractmethod
    def issue(self, subject: str, scope: TokenScope, **claims) -> str: ...

    @abstractmethod
    def decode(self, token: str, expected_scope: TokenScope) -> TokenClaims: ...


class ReplayCache(ABC):
    @abstractmethod
    def was_used(self, user_id: str, code: str) -> bool: ...

    @abstractmethod
    def mark_used(self, user_id: str, code: str) -> None:
        """Registra el código; lanza ReplayAttackDetected si ya existía."""


class SecretGenerator(ABC):
    @abstractmethod
    def totp_secret(self) -> str: ...

    @abstractmethod
    def backup_codes(self, count: int) -> list[str]: ...


class QrCodeRenderer(ABC):
    @abstractmethod
    def png_base64(self, data: str) -> str: ...


class Clock(ABC):
    @abstractmethod
    def now(self) -> float: ...
