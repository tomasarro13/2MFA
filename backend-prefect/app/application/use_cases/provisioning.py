"""Process Manager del aprovisionamiento 2FA: DISABLED -> PENDING_VERIFICATION -> ACTIVE."""
from ...domain import totp
from ...domain.entities import MfaStatus, User
from ...domain.exceptions import InvalidMfaState, UserNotFound
from ..dto import ActivationResult, ProvisioningResult
from ..ports import BackupCodeHasher, QrCodeRenderer, ReplayCache, SecretGenerator, UserRepository

BACKUP_CODES_COUNT = 8


def _load(users: UserRepository, user_id: str) -> User:
    user = users.get_by_id(user_id)
    if not user:
        raise UserNotFound(user_id)
    return user


class StartMfaProvisioning:
    def __init__(self, users: UserRepository, secrets: SecretGenerator, backup_hasher: BackupCodeHasher,
                 qr: QrCodeRenderer, issuer: str):
        self._users = users
        self._secrets = secrets
        self._backup_hasher = backup_hasher
        self._qr = qr
        self._issuer = issuer

    def execute(self, user_id: str) -> ProvisioningResult:
        user = _load(self._users, user_id)
        secret = self._secrets.totp_secret()
        backup_codes = self._secrets.backup_codes(BACKUP_CODES_COUNT)
        user.start_mfa_provisioning(secret, [self._backup_hasher.hash(c) for c in backup_codes])
        self._users.save(user)
        uri = totp.provisioning_uri(secret, user.username, self._issuer)
        return ProvisioningResult(
            secret=secret,
            otpauth_uri=uri,
            qr_png_base64=self._qr.png_base64(uri),
            backup_codes=backup_codes,
            mfa_status=user.mfa_status.value,
        )


class LoadPendingConfiguration:
    def __init__(self, users: UserRepository):
        self._users = users

    def execute(self, user_id: str) -> str:
        user = _load(self._users, user_id)
        if user.mfa_status is not MfaStatus.PENDING_VERIFICATION:
            raise InvalidMfaState(f"Se esperaba PENDING_VERIFICATION, estado actual: {user.mfa_status.value}")
        return user.id


class ActivateMfa:
    def __init__(self, users: UserRepository, replay_cache: ReplayCache):
        self._users = users
        self._replay_cache = replay_cache

    def execute(self, user_id: str, code: str) -> ActivationResult:
        user = _load(self._users, user_id)
        self._replay_cache.mark_used(user.id, code)
        previous = user.mfa_status.value
        user.activate_mfa()
        self._users.save(user)
        return ActivationResult(mfa_status=user.mfa_status.value,
                                detail=f"Estado {previous} -> {user.mfa_status.value}")
