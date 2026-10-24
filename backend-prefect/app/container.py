"""Composition Root: único lugar donde se eligen las implementaciones concretas."""
from dataclasses import dataclass

from .application.dto import TokenScope
from .application.ports import TokenService, UserRepository
from .application.strategy_registry import StrategyRegistry
from .application.use_cases.auth import IssueRestrictedToken, RegisterUser, VerifyCredentials
from .application.use_cases.provisioning import ActivateMfa, LoadPendingConfiguration, StartMfaProvisioning
from .application.use_cases.vault import AccessVault
from .application.use_cases.verification import (
    CheckAntiReplay,
    ExecuteMfaStrategy,
    IssueElevatedSession,
    ValidatePreAuthState,
)
from .application.workflows import AuthSteps, AuthWorkflows, SequentialAuthWorkflows
from .domain.strategies import BackupCodeStrategy, TOTPStrategy
from .infrastructure.cache.in_memory_replay_cache import InMemoryReplayCache
from .infrastructure.config import Settings
from .infrastructure.persistence.sqlite_user_repository import SQLiteUserRepository
from .infrastructure.qr.qrcode_renderer import PngQrCodeRenderer
from .infrastructure.security.aes_secret_cipher import AesGcmSecretCipher
from .infrastructure.security.hashers import BcryptPasswordHasher, Sha256BackupCodeHasher
from .infrastructure.security.jwt_token_service import JwtTokenService
from .infrastructure.security.secret_generator import CryptoSecretGenerator
from .infrastructure.system_clock import SystemClock


@dataclass(frozen=True)
class Container:
    tokens: TokenService
    workflows: AuthWorkflows
    register_user: RegisterUser
    access_vault: AccessVault


def _build_repository(settings: Settings) -> UserRepository:
    cipher = AesGcmSecretCipher(settings.totp_encryption_key)
    if settings.supabase_url and settings.supabase_key:
        from .infrastructure.persistence.supabase_user_repository import SupabaseUserRepository

        return SupabaseUserRepository(settings.supabase_url, settings.supabase_key, cipher)
    return SQLiteUserRepository(settings.sqlite_path, cipher)


def build_container(settings: Settings, users: UserRepository | None = None) -> Container:
    users = users or _build_repository(settings)
    passwords = BcryptPasswordHasher()
    backup_hasher = Sha256BackupCodeHasher()
    replay_cache = InMemoryReplayCache(settings.replay_ttl_seconds)
    tokens = JwtTokenService(settings.jwt_secret, {
        TokenScope.PRE_AUTH: settings.pre_auth_ttl_seconds,
        TokenScope.MFA_SETUP: settings.pre_auth_ttl_seconds,
        TokenScope.ACCESS: settings.access_ttl_seconds,
    })
    strategies = StrategyRegistry([
        TOTPStrategy(clock=SystemClock().now),
        BackupCodeStrategy(hash_code=backup_hasher.hash),
    ])

    steps = AuthSteps(
        verify_credentials=VerifyCredentials(users, passwords),
        issue_restricted_token=IssueRestrictedToken(users, tokens),
        start_provisioning=StartMfaProvisioning(users, CryptoSecretGenerator(), backup_hasher,
                                                PngQrCodeRenderer(), settings.issuer),
        load_pending_configuration=LoadPendingConfiguration(users),
        activate_mfa=ActivateMfa(users, replay_cache),
        validate_pre_auth_state=ValidatePreAuthState(tokens, users),
        check_anti_replay=CheckAntiReplay(replay_cache),
        execute_mfa_strategy=ExecuteMfaStrategy(users, strategies),
        issue_elevated_session=IssueElevatedSession(replay_cache, tokens),
    )

    if settings.use_prefect:
        from .infrastructure.orchestration.prefect_workflows import PrefectAuthWorkflows

        workflows: AuthWorkflows = PrefectAuthWorkflows(steps)
    else:
        workflows = SequentialAuthWorkflows(steps)

    return Container(
        tokens=tokens,
        workflows=workflows,
        register_user=RegisterUser(users, passwords),
        access_vault=AccessVault(users),
    )
