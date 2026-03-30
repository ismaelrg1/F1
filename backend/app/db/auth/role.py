from __future__ import annotations

from sqlalchemy import String, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import List, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.auth import User, Permission

from app.db.enums import RoleName

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint("length(description) >= 2", name="ck_roles_desc_minlen"),
        CheckConstraint("length(description) <= 255", name="ck_roles_desc_len"),
        {"schema": "auth"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[RoleName] = mapped_column(Enum(RoleName, name="role_name_enum", schema="auth"),
                                            unique=True, 
                                            nullable=False
                                            )


    description: Mapped[str] = mapped_column(String(255), nullable=False)

    users: Mapped[List["User"]] = relationship(
        'User',
        secondary="auth.user_roles",
        back_populates="roles"
    )

    permissions: Mapped[List["Permission"]] = relationship(
        'Permission',
        secondary="auth.role_permissions",
        back_populates="roles"
    )
    
