import json
import sqlite3
import threading
import uuid

from ...application.ports import SecretCipher, UserRepository
from ...domain.entities import User
from .mapper import row_to_user, user_to_mutable_fields

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    mfa_status TEXT NOT NULL DEFAULT 'DISABLED',
    totp_secret TEXT,
    backup_codes TEXT NOT NULL DEFAULT '[]'
)
"""


class SQLiteUserRepository(UserRepository):
    """Alternativa local a Supabase para trabajar sin conexión."""

    def __init__(self, path: str, cipher: SecretCipher):
        self._cipher = cipher
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(_SCHEMA)
            self._conn.commit()

    def _find_one(self, column: str, value: str) -> User | None:
        with self._lock:
            row = self._conn.execute(f"SELECT * FROM users WHERE {column} = ?", (value,)).fetchone()
        return row_to_user(dict(row), self._cipher) if row else None

    def add(self, username: str, password_hash: str) -> User:
        user = User(id=str(uuid.uuid4()), username=username, password_hash=password_hash)
        with self._lock:
            self._conn.execute(
                "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
                (user.id, user.username, user.password_hash),
            )
            self._conn.commit()
        return user

    def get_by_id(self, user_id: str) -> User | None:
        return self._find_one("id", user_id)

    def get_by_username(self, username: str) -> User | None:
        return self._find_one("username", username)

    def save(self, user: User) -> None:
        fields = user_to_mutable_fields(user, self._cipher)
        fields["backup_codes"] = json.dumps(fields["backup_codes"])
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self._lock:
            self._conn.execute(f"UPDATE users SET {cols} WHERE id = ?", (*fields.values(), user.id))
            self._conn.commit()
