import json

from ...application.ports import SecretCipher
from ...domain.entities import MfaStatus, User


def row_to_user(row: dict, cipher: SecretCipher) -> User:
    codes = row.get("backup_codes") or []
    if isinstance(codes, str):
        codes = json.loads(codes)
    user_id = str(row["id"])
    encrypted_secret = row.get("totp_secret")
    return User(
        id=user_id,
        username=row["username"],
        password_hash=row["password_hash"],
        mfa_status=MfaStatus(row.get("mfa_status") or MfaStatus.DISABLED.value),
        # El id va como dato asociado: un secreto copiado a otra fila no descifra.
        totp_secret=cipher.decrypt(encrypted_secret, user_id) if encrypted_secret else None,
        backup_code_hashes=list(codes),
    )


def user_to_mutable_fields(user: User, cipher: SecretCipher) -> dict:
    return {
        "mfa_status": user.mfa_status.value,
        "totp_secret": cipher.encrypt(user.totp_secret, user.id) if user.totp_secret else None,
        "backup_codes": list(user.backup_code_hashes),
    }
