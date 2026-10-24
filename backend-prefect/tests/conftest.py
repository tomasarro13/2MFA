import pytest
from fastapi.testclient import TestClient

from app.container import build_container
from app.infrastructure.config import Settings
from app.infrastructure.persistence.sqlite_user_repository import SQLiteUserRepository
from app.infrastructure.security.aes_secret_cipher import AesGcmSecretCipher
from app.main import create_app


TEST_TOTP_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def make_settings(use_prefect: bool = False, replay_ttl_seconds: int = 90) -> Settings:
    return Settings(
        jwt_secret="test-secret-de-al-menos-32-bytes-ok!", totp_encryption_key=TEST_TOTP_KEY,
        issuer="Lab2FA", pre_auth_ttl_seconds=300, access_ttl_seconds=3600,
        replay_ttl_seconds=replay_ttl_seconds, supabase_url=None, supabase_key=None, sqlite_path=":memory:",
        use_prefect=use_prefect,
    )


def make_client(**settings) -> TestClient:
    container = build_container(make_settings(**settings), users=SQLiteUserRepository(":memory:", AesGcmSecretCipher(TEST_TOTP_KEY)))
    return TestClient(create_app(container))


@pytest.fixture
def client() -> TestClient:
    return make_client()
