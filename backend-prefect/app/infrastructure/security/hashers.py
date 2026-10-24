import hashlib

import bcrypt

from ...application.ports import BackupCodeHasher, PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())


class Sha256BackupCodeHasher(BackupCodeHasher):
    def hash(self, code: str) -> str:
        return hashlib.sha256(code.strip().upper().encode()).hexdigest()
