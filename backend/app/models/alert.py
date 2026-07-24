from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, Base, TimestampMixin, UUIDMixin


class Alert(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "alerts"

    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # low|medium|high|critical
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)

    user_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="open", index=True)  # open|investigating|resolved|dismissed
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    resolved_by_id: Mapped[str | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user: Mapped["User | None"] = relationship(foreign_keys=[user_id], lazy="selectin")  # noqa: F821
