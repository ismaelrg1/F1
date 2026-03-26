from __future__ import annotations

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        Index("ix_user_roles_role_id", "role_id"),
        Index("ix_user_roles_user_id", "user_id"),
        {"schema": "auth"},
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True)

    role_id: Mapped[int] = mapped_column(ForeignKey("auth.roles.id", ondelete="CASCADE"), primary_key=True)


    
