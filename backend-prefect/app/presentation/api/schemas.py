from pydantic import BaseModel, Field


class CredentialsIn(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=4)


class CodeIn(BaseModel):
    code: str = Field(min_length=6)


class Verify2FAIn(BaseModel):
    pre_auth_token: str
    code: str = Field(min_length=6)
    method: str = "totp"  # "totp" | "backup"


class UserOut(BaseModel):
    id: str
    username: str
    mfa_status: str
