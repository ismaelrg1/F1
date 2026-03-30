from __future__ import annotations

from datetime import datetime
import enum
from sqlalchemy import func, Index, Enum, DateTime, UniqueConstraint, ForeignKey, ForeignKeyConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.social import Group, Team
    from app.db.auth import User

class TeamRole(str, enum.Enum):
    CAPTAIN = "CAPTAIN"
    MEMBER = "MEMBER"

class TeamMembership(Base):
    __tablename__ = "team_memberships"
    __table_args__ = (
        # Un usuario no puede repetirse en el mismo equipo
        UniqueConstraint("team_id", "user_id", name="uq_team_memberships_team_user"),
        # Un usuario solo puede pertenecer a un equipo por grupo
        UniqueConstraint("group_id", "user_id", name="uq_team_memberships_group_user"),
        ForeignKeyConstraint(
            ["group_id", "team_id"],
            ["social.teams.group_id", "social.teams.id"],
            ondelete="CASCADE",
            name="fk_team_memberships_group_team",
        ),

        # Lookups
        Index("ix_team_memberships_team_id", "team_id"),
        Index("ix_team_memberships_user_id", "user_id"),
        Index("ix_team_memberships_group_id", "group_id"),
        Index(
            "uq_team_memberships_single_captain",
            "team_id",
            unique=True,
            postgresql_where=text("role = 'CAPTAIN'"),
        ),

        {"schema": "social"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_id: Mapped[int] = mapped_column(
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole, name="team_role_enum", schema="social"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    group: Mapped["Group"] = relationship(
        "app.db.social.group.Group",
        overlaps="team,team_memberships",
    )

    team: Mapped["Team"] = relationship(
        "app.db.social.team.Team",
        back_populates="team_memberships",
        overlaps="group",
    )

    user: Mapped["User"] = relationship(
        "app.db.auth.user.User",
        back_populates="team_memberships",
    )

