from __future__ import annotations

from datetime import datetime
import enum
from sqlalchemy import func, Index, Enum, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.social import Team
    from app.db.auth import User

class TeamRole(str, enum.Enum):
    CAPTAIN = "CAPTAIN"
    MEMBER = "MEMBER"

class TeamMembership(Base):
    __tablename__ = "team_memberships"
    __table_args__ = (
        # Un usuario no puede repetirse en el mismo equipo
        UniqueConstraint("team_id", "user_id", name="uq_team_memberships_team_user"),

        # Lookups
        Index("ix_team_memberships_team_id", "team_id"),
        Index("ix_team_memberships_user_id", "user_id"),

        {"schema": "social"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("social.teams.id", ondelete="CASCADE"),
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

    team: Mapped["Team"] = relationship(
        "app.db.social.team.Team",
        back_populates="team_memberships",
    )

    user: Mapped["User"] = relationship(
        "app.db.auth.user.User",
        back_populates="team_memberships",
    )

