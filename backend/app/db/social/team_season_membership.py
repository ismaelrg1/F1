from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base
from app.db.social.team_membership import TeamRole

if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.competition import Season
    from app.db.social import Group, Team


class TeamSeasonMembership(Base):
    __tablename__ = "team_season_memberships"
    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "season_id",
            "user_id",
            name="uq_team_season_memberships_team_season_user",
        ),
        UniqueConstraint(
            "group_id",
            "season_id",
            "user_id",
            name="uq_team_season_memberships_group_season_user",
        ),
        ForeignKeyConstraint(
            ["group_id", "team_id"],
            ["social.teams.group_id", "social.teams.id"],
            ondelete="CASCADE",
            name="fk_team_season_memberships_group_team",
        ),
        CheckConstraint(
            "active_from IS NULL OR active_to IS NULL OR active_from < active_to",
            name="ck_team_season_memberships_active_window",
        ),
        Index("ix_team_season_memberships_group_season", "group_id", "season_id"),
        Index("ix_team_season_memberships_team_id", "team_id"),
        Index("ix_team_season_memberships_user_id", "user_id"),
        Index(
            "ix_team_season_memberships_active",
            "group_id",
            "season_id",
            "is_active",
        ),
        {"schema": "social"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_id: Mapped[int] = mapped_column(nullable=False)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole, name="team_role_enum", schema="social", create_type=False),
        nullable=False,
        server_default=text("'MEMBER'"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    active_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    active_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    group: Mapped["Group"] = relationship("Group")

    season: Mapped["Season"] = relationship("Season")

    team: Mapped["Team"] = relationship("Team", overlaps="group")

    user: Mapped["User"] = relationship("User")
