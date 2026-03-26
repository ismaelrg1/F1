from __future__ import annotations

from datetime import datetime
import enum

from sqlalchemy import UniqueConstraint, Index, func, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.social import Group
    from app.db.auth import User

class GroupRole(str, enum.Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"
    MODERATOR = "MODERATOR"


class GroupMembership(Base):
    __tablename__ = "group_memberships"
    __table_args__ = (
        # 1) Un usuario solo puede estar 1 vez en el mismo grupo
        UniqueConstraint(
            "group_id",
            "user_id",
            name="uq_group_memberships_group_user",
        ),

        # 2) Índices típicos
        Index("ix_group_memberships_group_id", "group_id"),
        Index("ix_group_memberships_user_id", "user_id"),
        Index("ix_group_memberships_group_role", "group_id", "role"),

        {"schema": "social"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[GroupRole] = mapped_column(
        Enum(GroupRole, name="group_role_enum", schema="social"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(
        'User',
        back_populates="group_memberships",
    )

    group: Mapped["Group"] = relationship(
        'Group',
        back_populates="group_memberships",
    )

