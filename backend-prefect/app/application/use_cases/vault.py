from ...domain.exceptions import MfaRequired, UserNotFound
from ..dto import TokenClaims, VaultContent
from ..ports import UserRepository


class AccessVault:
    def __init__(self, users: UserRepository):
        self._users = users

    def execute(self, claims: TokenClaims) -> VaultContent:
        if not claims.mfa_verified:
            raise MfaRequired("Se requiere una sesión con mfa_verified=true")
        user = self._users.get_by_id(claims.subject)
        if not user:
            raise UserNotFound(claims.subject)
        return VaultContent(
            mensaje=f"Bienvenido a la bóveda, {user.username}",
            secreto="El tesoro está enterrado bajo el edificio K de la Sabana",
            amr=list(claims.amr),
        )
