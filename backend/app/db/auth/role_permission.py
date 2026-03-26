from __future__ import annotations

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = __table_args__ = (
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
        {"schema": "auth"},
    )

    permission_id: Mapped[int] = mapped_column(ForeignKey("auth.permissions.id", ondelete="CASCADE"), primary_key=True)

    role_id: Mapped[int] = mapped_column(ForeignKey("auth.roles.id", ondelete="CASCADE"), primary_key=True)

    
    
