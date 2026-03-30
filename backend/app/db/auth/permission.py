from __future__ import annotations

from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.auth import Role


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        CheckConstraint("code ~ '^[A-Z0-9_]+$'", name="ck_permissions_code_format"),
        CheckConstraint("length(description) >= 2", name="ck_permissions_desc_minlen"),
        CheckConstraint("length(description) <= 255", name="ck_permissions_desc_len"),
        {"schema": "auth"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    roles: Mapped[List["Role"]] = relationship(
        'Role',
        secondary="auth.role_permissions",
        back_populates="permissions",
        passive_deletes=True
    )
    
