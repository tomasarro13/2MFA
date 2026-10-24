from ...application.ports import SecretCipher, UserRepository
from ...domain.entities import MfaStatus, User
from .mapper import row_to_user, user_to_mutable_fields


class SupabaseUserRepository(UserRepository):
    TABLE = "users"

    def __init__(self, url: str, key: str, cipher: SecretCipher):
        self._cipher = cipher
        from supabase import create_client

        self._client = create_client(url, key)

    def _find_one(self, column: str, value: str) -> User | None:
        res = self._client.table(self.TABLE).select("*").eq(column, value).limit(1).execute()
        return row_to_user(res.data[0], self._cipher) if res.data else None

    def add(self, username: str, password_hash: str) -> User:
        res = (
            self._client.table(self.TABLE)
            .insert({"username": username, "password_hash": password_hash,
                     "mfa_status": MfaStatus.DISABLED.value})
            .execute()
        )
        return row_to_user(res.data[0], self._cipher)

    def get_by_id(self, user_id: str) -> User | None:
        return self._find_one("id", user_id)

    def get_by_username(self, username: str) -> User | None:
        return self._find_one("username", username)

    def save(self, user: User) -> None:
        self._client.table(self.TABLE).update(user_to_mutable_fields(user, self._cipher)).eq("id", user.id).execute()
