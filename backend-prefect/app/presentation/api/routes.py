from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from ...application.dto import TokenClaims, TokenScope
from ...container import Container
from .dependencies import get_container, require_scope
from .schemas import CodeIn, CredentialsIn, UserOut, Verify2FAIn

WEB_DIR = Path(__file__).resolve().parents[1] / "web"

router = APIRouter()


@router.get("/", include_in_schema=False)
def web_app():
    return FileResponse(WEB_DIR / "index.html")


@router.post("/auth/register", status_code=201, response_model=UserOut)
def register(body: CredentialsIn, c: Container = Depends(get_container)):
    user = c.register_user.execute(body.username, body.password)
    return UserOut(id=user.id, username=user.username, mfa_status=user.mfa_status.value)


@router.post("/auth/login")
def login(body: CredentialsIn, c: Container = Depends(get_container)):
    return asdict(c.workflows.login(body.username, body.password))


@router.post("/2fa/setup")
def setup_2fa(claims: TokenClaims = Depends(require_scope(TokenScope.MFA_SETUP)),
              c: Container = Depends(get_container)):
    return asdict(c.workflows.start_provisioning(claims.subject))


@router.post("/2fa/activate")
def activate_2fa(body: CodeIn, claims: TokenClaims = Depends(require_scope(TokenScope.MFA_SETUP)),
                 c: Container = Depends(get_container)):
    return asdict(c.workflows.confirm_provisioning(claims.subject, body.code.strip()))


@router.post("/auth/verify-2fa")
def verify_2fa(body: Verify2FAIn, c: Container = Depends(get_container)):
    return asdict(c.workflows.verify_2fa(body.pre_auth_token, body.code.strip(), body.method))


@router.get("/api/boveda-secreta")
def boveda(claims: TokenClaims = Depends(require_scope(TokenScope.ACCESS)),
           c: Container = Depends(get_container)):
    return asdict(c.access_vault.execute(claims))
