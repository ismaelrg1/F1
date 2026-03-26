from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Index, ForeignKey, DateTime,func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.auth import User


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("ix_password_reset_tokens_user_id", "user_id"),
        Index("ix_password_reset_tokens_expires_at", "expires_at"),
        {"schema": "auth"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.users.id", 
                   ondelete="CASCADE")
    )
    
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    invalidated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


    user: Mapped["User"] = relationship(
        "User",
        back_populates="password_reset_tokens",
    )
