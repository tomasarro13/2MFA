from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...application.dto import TokenClaims, TokenScope
from ...container import Container

_bearer = HTTPBearer()


def get_container(request: Request) -> Container:
    return request.app.state.container


def require_scope(scope: TokenScope):
    def dependency(
        creds: HTTPAuthorizationCredentials = Depends(_bearer),
        container: Container = Depends(get_container),
    ) -> TokenClaims:
        return container.tokens.decode(creds.credentials, scope)

    return dependency
