from dataclasses import dataclass, field
from enum import Enum

from .exceptions import InvalidMfaState


class MfaStatus(str, Enum):
    DISABLED = "DISABLED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"


# Máquina de estados del aprovisionamiento 2FA.
# PENDING -> PENDING permite regenerar el QR si el usuario nunca lo escaneó.
_TRANSITIONS: dict[MfaStatus, set[MfaStatus]] = {
    MfaStatus.DISABLED: {MfaStatus.PENDING_VERIFICATION},
    MfaStatus.PENDING_VERIFICATION: {MfaStatus.PENDING_VERIFICATION, MfaStatus.ACTIVE},
    MfaStatus.ACTIVE: set(),
}


@dataclass
class User:
    id: str
    username: str
    password_hash: str
    mfa_status: MfaStatus = MfaStatus.DISABLED
    totp_secret: str | None = None
    backup_code_hashes: list[str] = field(default_factory=list)

    @property
    def mfa_active(self) -> bool:
        return self.mfa_status is MfaStatus.ACTIVE

    def _transition(self, target: MfaStatus) -> None:
        if target not in _TRANSITIONS[self.mfa_status]:
            raise InvalidMfaState(f"Transición no permitida: {self.mfa_status.value} -> {target.value}")
        self.mfa_status = target

    def start_mfa_provisioning(self, totp_secret: str, backup_code_hashes: list[str]) -> None:
        self._transition(MfaStatus.PENDING_VERIFICATION)
        self.totp_secret = totp_secret
        self.backup_code_hashes = list(backup_code_hashes)

    def activate_mfa(self) -> None:
        self._transition(MfaStatus.ACTIVE)

    def consume_backup_code(self, code_hash: str) -> None:
        self.backup_code_hashes.remove(code_hash)
