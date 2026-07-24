from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain a lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a digit")
        if not any(not c.isalnum() for c in v):
            raise ValueError("Password must contain a special character")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    mfa_required: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_url: str


class MfaEnableRequest(BaseModel):
    code: str


class MfaDisableRequest(BaseModel):
    code: str


class SessionOut(BaseModel):
    id: str
    ip_address: str | None
    user_agent: str | None
    device: str | None
    created_at: datetime
    expires_at: datetime
    revoked: bool

    class Config:
        from_attributes = True
