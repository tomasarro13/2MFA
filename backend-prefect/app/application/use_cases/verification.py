"""Pasos del pipeline de verificación del segundo factor (uno por responsabilidad)."""
from ...domain.exceptions import InvalidSecondFactor, InvalidToken, ReplayAttackDetected
from ..dto import SessionResult, StrategyOutcome, TokenScope
from ..ports import ReplayCache, TokenService, UserRepository
from ..strategy_registry import StrategyRegistry


class ValidatePreAuthState:
    def __init__(self, tokens: TokenService, users: UserRepository):
        self._tokens = tokens
        self._users = users

    def execute(self, pre_auth_token: str) -> str:
        claims = self._tokens.decode(pre_auth_token, TokenScope.PRE_AUTH)
        user = self._users.get_by_id(claims.subject)
        if not user or not user.mfa_active:
            raise InvalidToken("El usuario no tiene 2FA activo")
        return user.id


class CheckAntiReplay:
    def __init__(self, replay_cache: ReplayCache):
        self._replay_cache = replay_cache

    def execute(self, user_id: str, code: str) -> None:
        if self._replay_cache.was_used(user_id, code):
            raise ReplayAttackDetected(f"El código {code} ya fue utilizado en los últimos 90 s")


class ExecuteMfaStrategy:
    def __init__(self, users: UserRepository, strategies: StrategyRegistry):
        self._users = users
        self._strategies = strategies

    def execute(self, user_id: str, code: str, method: str) -> StrategyOutcome:
        strategy = self._strategies.get(method)
        user = self._users.get_by_id(user_id)
        result = strategy.verify(user, code)
        if not result.ok:
            raise InvalidSecondFactor(result.detail)
        if result.consumed_backup_hash:
            user.consume_backup_code(result.consumed_backup_hash)
            self._users.save(user)
        return StrategyOutcome(method=strategy.name, detail=result.detail, window_offset=result.window_offset)


class IssueElevatedSession:
    def __init__(self, replay_cache: ReplayCache, tokens: TokenService):
        self._replay_cache = replay_cache
        self._tokens = tokens

    def execute(self, user_id: str, code: str, method: str) -> SessionResult:
        self._replay_cache.mark_used(user_id, code)
        token = self._tokens.issue(user_id, TokenScope.ACCESS, mfa_verified=True, amr=[method])
        return SessionResult(access_token=token, mfa_verified=True)
