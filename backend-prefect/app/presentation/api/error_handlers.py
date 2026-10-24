from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ...domain import exceptions as e

_STATUS_BY_ERROR: dict[type[e.DomainError], int] = {
    e.InvalidCredentials: 401,
    e.InvalidToken: 401,
    e.InvalidSecondFactor: 401,
    e.MfaRequired: 403,
    e.UserNotFound: 404,
    e.ReplayAttackDetected: 409,
    e.UserAlreadyExists: 409,
    e.InvalidMfaState: 400,
    e.UnknownMfaMethod: 400,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(e.DomainError)
    async def handle_domain_error(_: Request, exc: e.DomainError):
        status = _STATUS_BY_ERROR.get(type(exc), 400)
        return JSONResponse(status_code=status, content={"error": type(exc).__name__, "detail": str(exc)})
