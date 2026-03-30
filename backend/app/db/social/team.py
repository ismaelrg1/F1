from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, text, String, Boolean, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, List

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.social import TeamMembership, Group
    from app.db.scoring import TeamSeasonAggregate, TeamEventAggregate
    from app.db.powerups import PowerUpUseTarget

class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("group_id", "name", name="uq_teams_group_name"),
        UniqueConstraint("group_id", "id", name="uq_teams_group_id_id"),
        Index("ix_teams_group_id", "group_id"),
        Index("ix_teams_group_active", "group_id", "is_active"),
        Index("ix_teams_public_id", "public_id"),
        CheckConstraint("length(name) >= 2", name="ck_teams_name_minlen"),
        {"schema": "social"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid4,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    group: Mapped["Group"] = relationship(
        'Group',
        back_populates="teams",
    )

    team_memberships: Mapped[List["TeamMembership"]] = relationship(
        'TeamMembership',
        back_populates="team",
        cascade="all, delete-orphan",
    )

    team_season_aggregates: Mapped[list["TeamSeasonAggregate"]] = relationship(
        "TeamSeasonAggregate",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    team_event_aggregates: Mapped[list["TeamEventAggregate"]] = relationship(
        "TeamEventAggregate",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    powerup_targets_received: Mapped[list["PowerUpUseTarget"]] = relationship(
        "PowerUpUseTarget",
        foreign_keys="PowerUpUseTarget.target_team_id",
        back_populates="target_team",
    )
