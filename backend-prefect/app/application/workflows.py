"""Workflows de autenticación: definen el orden de los pasos.

`AuthWorkflows` es la abstracción que consume la capa de presentación (DIP).
`SequentialAuthWorkflows` los ejecuta en proceso (útil en pruebas); la versión
orquestada y observable vive en infrastructure/orchestration (Prefect).
Ambas son intercambiables (LSP).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .dto import ActivationResult, LoginResult, ProvisioningResult, SessionResult
from .use_cases.auth import IssueRestrictedToken, VerifyCredentials
from .use_cases.provisioning import ActivateMfa, LoadPendingConfiguration, StartMfaProvisioning
from .use_cases.verification import CheckAntiReplay, ExecuteMfaStrategy, IssueElevatedSession, ValidatePreAuthState


@dataclass(frozen=True)
class AuthSteps:
    verify_credentials: VerifyCredentials
    issue_restricted_token: IssueRestrictedToken
    start_provisioning: StartMfaProvisioning
    load_pending_configuration: LoadPendingConfiguration
    activate_mfa: ActivateMfa
    validate_pre_auth_state: ValidatePreAuthState
    check_anti_replay: CheckAntiReplay
    execute_mfa_strategy: ExecuteMfaStrategy
    issue_elevated_session: IssueElevatedSession


class AuthWorkflows(ABC):
    @abstractmethod
    def login(self, username: str, password: str) -> LoginResult: ...

    @abstractmethod
    def start_provisioning(self, user_id: str) -> ProvisioningResult: ...

    @abstractmethod
    def confirm_provisioning(self, user_id: str, code: str) -> ActivationResult: ...

    @abstractmethod
    def verify_2fa(self, pre_auth_token: str, code: str, method: str) -> SessionResult: ...


class SequentialAuthWorkflows(AuthWorkflows):
    def __init__(self, steps: AuthSteps):
        self._s = steps

    def login(self, username: str, password: str) -> LoginResult:
        user_id = self._s.verify_credentials.execute(username, password)
        return self._s.issue_restricted_token.execute(user_id)

    def start_provisioning(self, user_id: str) -> ProvisioningResult:
        return self._s.start_provisioning.execute(user_id)

    def confirm_provisioning(self, user_id: str, code: str) -> ActivationResult:
        self._s.load_pending_configuration.execute(user_id)
        self._s.check_anti_replay.execute(user_id, code)
        self._s.execute_mfa_strategy.execute(user_id, code, "totp")
        return self._s.activate_mfa.execute(user_id, code)

    def verify_2fa(self, pre_auth_token: str, code: str, method: str) -> SessionResult:
        user_id = self._s.validate_pre_auth_state.execute(pre_auth_token)
        self._s.check_anti_replay.execute(user_id, code)
        outcome = self._s.execute_mfa_strategy.execute(user_id, code, method)
        return self._s.issue_elevated_session.execute(user_id, code, outcome.method)
