import pytest

from app.domain import totp
from app.domain.entities import MfaStatus, User
from app.domain.exceptions import InvalidMfaState
from app.domain.strategies import BackupCodeStrategy, TOTPStrategy

SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
NOW = 1_700_000_000


def active_user() -> User:
    return User("1", "ana", "x", MfaStatus.ACTIVE, SECRET, ["h:ABC"])


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_totp_strategy_accepts_adjacent_windows(offset):
    code = totp.totp(SECRET, NOW + offset * 30)
    result = TOTPStrategy(clock=lambda: NOW).verify(active_user(), code)
    assert result.ok and result.window_offset == offset


def test_totp_strategy_rejects_code_two_windows_away():
    code = totp.totp(SECRET, NOW + 60)
    assert not TOTPStrategy(clock=lambda: NOW).verify(active_user(), code).ok


def test_backup_strategy_reports_consumed_hash():
    strategy = BackupCodeStrategy(hash_code=lambda c: f"h:{c}")
    assert strategy.verify(active_user(), "ABC").consumed_backup_hash == "h:ABC"
    assert not strategy.verify(active_user(), "ZZZ").ok


def test_state_machine_disabled_pending_active():
    user = User("1", "ana", "x")
    user.start_mfa_provisioning(SECRET, [])
    assert user.mfa_status is MfaStatus.PENDING_VERIFICATION
    user.activate_mfa()
    assert user.mfa_active


def test_cannot_activate_without_pending_state():
    with pytest.raises(InvalidMfaState):
        User("1", "ana", "x").activate_mfa()


def test_cannot_reprovision_active_user():
    with pytest.raises(InvalidMfaState):
        active_user().start_mfa_provisioning(SECRET, [])
