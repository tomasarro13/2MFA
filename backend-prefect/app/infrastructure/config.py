import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    totp_encryption_key: str
    issuer: str
    pre_auth_ttl_seconds: int
    access_ttl_seconds: int
    replay_ttl_seconds: int
    supabase_url: str | None
    supabase_key: str | None
    sqlite_path: str
    use_prefect: bool

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            jwt_secret=os.getenv("JWT_SECRET", "cambia-esto-en-tu-env-por-uno-de-32+-bytes"),
            totp_encryption_key=os.environ["TOTP_ENCRYPTION_KEY"],
            issuer=os.getenv("TOTP_ISSUER", "Lab2FA"),
            pre_auth_ttl_seconds=int(os.getenv("PRE_AUTH_TTL_SECONDS", "300")),
            access_ttl_seconds=int(os.getenv("ACCESS_TTL_SECONDS", "3600")),
            replay_ttl_seconds=int(os.getenv("REPLAY_TTL_SECONDS", "90")),
            supabase_url=os.getenv("SUPABASE_URL") or None,
            supabase_key=os.getenv("SUPABASE_KEY") or None,
            sqlite_path=os.getenv("SQLITE_PATH", "users.db"),
            use_prefect=os.getenv("USE_PREFECT", "true").lower() == "true",
        )
