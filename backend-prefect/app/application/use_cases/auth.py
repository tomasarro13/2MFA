from ...domain.exceptions import InvalidCredentials, UserAlreadyExists, UserNotFound
from ..dto import LoginResult, TokenScope
from ..ports import PasswordHasher, TokenService, UserRepository


class RegisterUser:
    def __init__(self, users: UserRepository, passwords: PasswordHasher):
        self._users = users
        self._passwords = passwords

    def execute(self, username: str, password: str):
        if self._users.get_by_username(username):
            raise UserAlreadyExists(f"El usuario '{username}' ya existe")
        return self._users.add(username, self._passwords.hash(password))


class VerifyCredentials:
    def __init__(self, users: UserRepository, passwords: PasswordHasher):
        self._users = users
        self._passwords = passwords

    def execute(self, username: str, password: str) -> str:
        user = self._users.get_by_username(username)
        if not user or not self._passwords.verify(password, user.password_hash):
            raise InvalidCredentials("Usuario o contraseña incorrectos")
        return user.id


class IssueRestrictedToken:
    """Step-Up: el login nunca entrega un access_token, solo tokens de alcance restringido."""

    def __init__(self, users: UserRepository, tokens: TokenService):
        self._users = users
        self._tokens = tokens

    def execute(self, user_id: str) -> LoginResult:
        user = self._users.get_by_id(user_id)
        if not user:
            raise UserNotFound(user_id)
        if user.mfa_active:
            return LoginResult(
                status="MFA_REQUIRED",
                mfa_status=user.mfa_status.value,
                pre_auth_token=self._tokens.issue(user.id, TokenScope.PRE_AUTH),
            )
        return LoginResult(
            status="MFA_SETUP_REQUIRED",
            mfa_status=user.mfa_status.value,
            setup_token=self._tokens.issue(user.id, TokenScope.MFA_SETUP),
        )

