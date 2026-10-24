from dataclasses import dataclass
from enum import Enum


class TokenScope(str, Enum):
    PRE_AUTH = "pre_auth"    # solo sirve para POST /auth/verify-2fa
    MFA_SETUP = "mfa_setup"  # solo sirve para aprovisionar 2FA
    ACCESS = "access"        # acceso a recursos protegidos


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    scope: TokenScope
    mfa_verified: bool = False
    amr: tuple[str, ...] = ()


@dataclass(frozen=True)
class LoginResult:
    status: str  # MFA_REQUIRED | MFA_SETUP_REQUIRED
    mfa_status: str
    pre_auth_token: str | None = None
    setup_token: str | None = None


@dataclass(frozen=True)
class ProvisioningResult:
    secret: str
    otpauth_uri: str
    qr_png_base64: str
    backup_codes: list[str]
    mfa_status: str


@dataclass(frozen=True)
class ActivationResult:
    mfa_status: str
    detail: str


@dataclass(frozen=True)
class StrategyOutcome:
    method: str
    detail: str
    window_offset: int | None = None


@dataclass(frozen=True)
class SessionResult:
    access_token: str
    mfa_verified: bool
    token_type: str = "bearer"


@dataclass(frozen=True)
class VaultContent:
    mensaje: str
    secreto: str
    amr: list[str]
