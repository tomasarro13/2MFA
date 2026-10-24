import time

import jwt

from ...application.dto import TokenClaims, TokenScope
from ...application.ports import TokenService
from ...domain.exceptions import InvalidToken


class JwtTokenService(TokenService):
    ALGORITHM = "HS256"

    def __init__(self, secret: str, ttl_by_scope: dict[TokenScope, int]):
        self._secret = secret
        self._ttl_by_scope = ttl_by_scope

    def issue(self, subject: str, scope: TokenScope, **claims) -> str:
        now = int(time.time())
        payload = {"sub": subject, "scope": scope.value, "iat": now,
                   "exp": now + self._ttl_by_scope[scope], **claims}
        return jwt.encode(payload, self._secret, algorithm=self.ALGORITHM)

    def decode(self, token: str, expected_scope: TokenScope) -> TokenClaims:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self.ALGORITHM])
        except jwt.PyJWTError as exc:
            raise InvalidToken(f"Token inválido: {exc}") from exc
        if payload.get("scope") != expected_scope.value:
            raise InvalidToken(f"Scope '{payload.get('scope')}' no permitido, se esperaba '{expected_scope.value}'")
        return TokenClaims(
            subject=payload["sub"],
            scope=expected_scope,
            mfa_verified=bool(payload.get("mfa_verified", False)),
            amr=tuple(payload.get("amr", ())),
        )
