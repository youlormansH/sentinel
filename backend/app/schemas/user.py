from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    mfa_enabled: bool
    last_login_at: datetime | None
    created_at: datetime
    threat_score: int

    class Config:
        from_attributes = True

    @field_validator("role", mode="before")
    @classmethod
    def _extract_role_name(cls, v):
        return v.name if hasattr(v, "name") else v


class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=10, max_length=128)
    role: str


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)
