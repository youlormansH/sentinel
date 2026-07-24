from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role_id: Mapped[str] = mapped_column(GUID(), ForeignKey("roles.id"), nullable=False)
    role: Mapped["Role"] = relationship(back_populates="users", lazy="selectin")  # noqa: F821

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # MFA (TOTP)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret_encrypted: Mapped[str | None] = mapped_column(String(255), nullable=True)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_login_country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    threat_score: Mapped[int] = mapped_column(default=0)

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.name if self.role else None,
            "is_active": self.is_active,
            "is_email_verified": self.is_email_verified,
            "mfa_enabled": self.mfa_enabled,
            "last_login_at": self.last_login_at,
            "created_at": self.created_at,
            "threat_score": self.threat_score,
        }
