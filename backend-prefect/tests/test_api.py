import time

from app.domain import totp

from .conftest import make_client


def provision(client, username="ana", password="clave123"):
    client.post("/auth/register", json={"username": username, "password": password})
    login = client.post("/auth/login", json={"username": username, "password": password}).json()
    assert login["status"] == "MFA_SETUP_REQUIRED" and "access_token" not in login
    headers = {"Authorization": f"Bearer {login['setup_token']}"}
    setup = client.post("/2fa/setup", headers=headers).json()
    assert setup["mfa_status"] == "PENDING_VERIFICATION"
    # Código de la ventana anterior para no chocar con el usado luego en verify-2fa
    first_code = totp.totp(setup["secret"], time.time() - 30)
    activated = client.post("/2fa/activate", headers=headers, json={"code": first_code})
    assert activated.json()["mfa_status"] == "ACTIVE"
    return setup


def pre_auth(client, username="ana", password="clave123"):
    r = client.post("/auth/login", json={"username": username, "password": password}).json()
    assert r["status"] == "MFA_REQUIRED"
    return r["pre_auth_token"]


def test_full_step_up_flow_and_replay_protection(client):
    setup = provision(client)
    code = totp.totp(setup["secret"], time.time())

    token = pre_auth(client)
    # El pre_auth_token no abre la bóveda
    assert client.get("/api/boveda-secreta", headers={"Authorization": f"Bearer {token}"}).status_code == 401

    session = client.post("/auth/verify-2fa", json={"pre_auth_token": token, "code": code}).json()
    assert session["mfa_verified"] is True
    vault = client.get("/api/boveda-secreta", headers={"Authorization": f"Bearer {session['access_token']}"})
    assert vault.status_code == 200 and vault.json()["amr"] == ["totp"]

    replay = client.post("/auth/verify-2fa", json={"pre_auth_token": pre_auth(client), "code": code})
    assert replay.status_code == 409 and replay.json()["error"] == "ReplayAttackDetected"


def test_backup_code_is_single_use():
    # Sin caché anti-replay, el segundo intento falla solo porque el código se consumió
    client = make_client(replay_ttl_seconds=-1)
    setup = provision(client)
    backup = setup["backup_codes"][0]
    ok = client.post("/auth/verify-2fa", json={"pre_auth_token": pre_auth(client), "code": backup, "method": "backup"})
    assert ok.status_code == 200 and ok.json()["mfa_verified"]
    again = client.post("/auth/verify-2fa", json={"pre_auth_token": pre_auth(client), "code": backup, "method": "backup"})
    assert again.status_code == 401 and again.json()["error"] == "InvalidSecondFactor"


def test_wrong_password_and_wrong_code(client):
    provision(client)
    assert client.post("/auth/login", json={"username": "ana", "password": "mala"}).status_code == 401
    bad = client.post("/auth/verify-2fa", json={"pre_auth_token": pre_auth(client), "code": "000000"})
    assert bad.status_code == 401


def test_setup_token_cannot_be_used_as_pre_auth(client):
    client.post("/auth/register", json={"username": "bob", "password": "clave123"})
    setup_token = client.post("/auth/login", json={"username": "bob", "password": "clave123"}).json()["setup_token"]
    r = client.post("/auth/verify-2fa", json={"pre_auth_token": setup_token, "code": "123456"})
    assert r.status_code == 401
