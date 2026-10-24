import pytest
from cryptography.exceptions import InvalidTag

from app.infrastructure.persistence.sqlite_user_repository import SQLiteUserRepository
from app.infrastructure.security.aes_secret_cipher import AesGcmSecretCipher
from tests.conftest import TEST_TOTP_KEY

SECRET = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"


def test_roundtrip_y_nonce_aleatorio():
    cipher = AesGcmSecretCipher(TEST_TOTP_KEY)
    a, b = cipher.encrypt(SECRET, "user-1"), cipher.encrypt(SECRET, "user-1")
    assert a != b
    assert cipher.decrypt(a, "user-1") == SECRET


def test_no_descifra_con_otro_contexto():
    cipher = AesGcmSecretCipher(TEST_TOTP_KEY)
    with pytest.raises(InvalidTag):
        cipher.decrypt(cipher.encrypt(SECRET, "user-1"), "user-2")


def test_la_bd_guarda_el_secreto_cifrado():
    repo = SQLiteUserRepository(":memory:", AesGcmSecretCipher(TEST_TOTP_KEY))
    user = repo.add("ana", "hash")
    user.start_mfa_provisioning(SECRET, [])
    repo.save(user)

    stored = repo._conn.execute("SELECT totp_secret FROM users").fetchone()[0]
    assert stored != SECRET
    assert repo.get_by_id(user.id).totp_secret == SECRET
