"""Adaptador de orquestación: envuelve cada paso de aplicación en un @task de
Prefect y los compone en @flows observables desde el dashboard.

Los casos de uso no conocen Prefect; este módulo es el único que lo importa.
"""
from prefect import flow, get_run_logger, task
from pydantic import SecretStr

from ...application.dto import ActivationResult, LoginResult, ProvisioningResult, SessionResult
from ...application.workflows import AuthSteps, AuthWorkflows


def _log_strategy_outcome(outcome) -> None:
    logger = get_run_logger()
    logger.info("Estrategia '%s': %s", outcome.method, outcome.detail)
    if outcome.window_offset:
        drift = "atrasado" if outcome.window_offset < 0 else "adelantado"
        logger.warning("El reloj del dispositivo parece %s ~30 s respecto al servidor", drift)


class PrefectAuthWorkflows(AuthWorkflows):
    def __init__(self, steps: AuthSteps):
        s = steps

        # ------------------------------------------------ Login (paso 1)
        @task
        def verify_credentials(username: str, password: SecretStr) -> str:
            user_id = s.verify_credentials.execute(username, password.get_secret_value())
            get_run_logger().info("Credenciales válidas para '%s'", username)
            return user_id

        @task
        def issue_restricted_token(user_id: str) -> LoginResult:
            result = s.issue_restricted_token.execute(user_id)
            get_run_logger().info("Estado MFA %s -> respuesta %s (sin access_token)",
                                  result.mfa_status, result.status)
            return result

        @flow(name="login-password", flow_run_name="login-{username}")
        def login_flow(username: str, password: SecretStr) -> LoginResult:
            return issue_restricted_token(verify_credentials(username, password))

        # ------------------------------ Aprovisionamiento (máquina de estados)
        @task
        def create_pending_configuration(user_id: str) -> ProvisioningResult:
            result = s.start_provisioning.execute(user_id)
            get_run_logger().info("Configuración 2FA creada en estado %s", result.mfa_status)
            return result

        @flow(name="mfa-provisioning-start", flow_run_name="setup-{user_id}")
        def start_provisioning_flow(user_id: str) -> ProvisioningResult:
            return create_pending_configuration(user_id)

        @task
        def load_pending_configuration(user_id: str) -> str:
            return s.load_pending_configuration.execute(user_id)

        @task
        def transition_to_active(user_id: str, code: str) -> ActivationResult:
            result = s.activate_mfa.execute(user_id, code)
            get_run_logger().info(result.detail)
            return result

        # ------------------------------------ Verificación 2FA (paso 2)
        @task
        def validate_pre_auth_state(pre_auth_token: SecretStr) -> str:
            user_id = s.validate_pre_auth_state.execute(pre_auth_token.get_secret_value())
            get_run_logger().info("pre_auth_token válido para el usuario %s", user_id)
            return user_id

        @task
        def check_anti_replay_cache(user_id: str, code: str) -> None:
            logger = get_run_logger()
            try:
                s.check_anti_replay.execute(user_id, code)
            except Exception as exc:
                logger.error("REPLAY ATTACK DETECTED: %s", exc)
                raise
            logger.info("Código no visto en la caché anti-replay")

        @task
        def execute_mfa_strategy(user_id: str, code: str, method: str) -> str:
            try:
                outcome = s.execute_mfa_strategy.execute(user_id, code, method)
            except Exception as exc:
                get_run_logger().error("Segundo factor rechazado: %s", exc)
                raise
            _log_strategy_outcome(outcome)
            return outcome.method

        @task
        def issue_elevated_session(user_id: str, code: str, method: str) -> SessionResult:
            result = s.issue_elevated_session.execute(user_id, code, method)
            get_run_logger().info("Código marcado como usado; access_token emitido con mfa_verified=true")
            return result

        @flow(name="mfa-provisioning-confirm", flow_run_name="activate-{user_id}")
        def confirm_provisioning_flow(user_id: str, code: str) -> ActivationResult:
            load_pending_configuration(user_id)
            check_anti_replay_cache(user_id, code)
            execute_mfa_strategy(user_id, code, "totp")
            return transition_to_active(user_id, code)

        @flow(name="verify-2fa", flow_run_name="verify-2fa-{method}")
        def verify_2fa_flow(pre_auth_token: SecretStr, code: str, method: str = "totp") -> SessionResult:
            user_id = validate_pre_auth_state(pre_auth_token)
            check_anti_replay_cache(user_id, code)
            used_method = execute_mfa_strategy(user_id, code, method)
            return issue_elevated_session(user_id, code, used_method)

        self._login_flow = login_flow
        self._start_provisioning_flow = start_provisioning_flow
        self._confirm_provisioning_flow = confirm_provisioning_flow
        self._verify_2fa_flow = verify_2fa_flow

    def login(self, username: str, password: str) -> LoginResult:
        return self._login_flow(username, SecretStr(password))

    def start_provisioning(self, user_id: str) -> ProvisioningResult:
        return self._start_provisioning_flow(user_id)

    def confirm_provisioning(self, user_id: str, code: str) -> ActivationResult:
        return self._confirm_provisioning_flow(user_id, code)

    def verify_2fa(self, pre_auth_token: str, code: str, method: str) -> SessionResult:
        return self._verify_2fa_flow(SecretStr(pre_auth_token), code, method)
