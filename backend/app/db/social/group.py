from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, text, String, Boolean, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, List, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.betting import BetContext
    from app.db.scoring import ScoreSeasonAggregate, TeamSeasonAggregate, TeamEventAggregate
    from app.db.social import GroupMembership, Team
    from app.db.powerups import PowerUpUseTarget, PowerUpUse, PowerUpAssignment
    from app.db.audit import AuditLog

class Group(Base):
    __tablename__ = "groups"
    __table_args__ = (
        UniqueConstraint("name", name="uq_groups_name"),
        UniqueConstraint("join_code", name="uq_groups_join_code"),
        Index("ix_groups_join_code", "join_code"),
        Index("ix_groups_public_id", "public_id"),
        CheckConstraint("length(name) >= 2", name="ck_groups_name_minlen"),
        CheckConstraint(
            "join_code IS NULL OR (length(join_code) >= 4 AND length(join_code) <= 20)",
            name="ck_groups_join_code_len",
        ),
        CheckConstraint(
            "max_team_size IS NULL OR max_team_size > 0",
            name="ck_groups_max_team_size_positive",
        ),
        CheckConstraint(
            "teams_enabled = true OR max_team_size IS NULL",
            name="ck_groups_max_team_size_requires_teams",
        ),
        {"schema": "social"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Código para unirse (solo si el grupo es privado)
    join_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_private: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    # Config de equipos (por grupo)
    teams_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    # NULL => sin límite (si teams_enabled=true)
    max_team_size: Mapped[Optional[int]] = mapped_column(nullable=True)


    bet_contexts: Mapped[List["BetContext"]] = relationship(
        'BetContext',
        back_populates="group",
    )

    score_season_aggregates: Mapped[list["ScoreSeasonAggregate"]] = relationship(
        "ScoreSeasonAggregate",
        back_populates="group",
    )

    group_memberships: Mapped[List["GroupMembership"]] = relationship(
        'GroupMembership',
        back_populates="group",
        cascade="all, delete-orphan",
    )

    teams: Mapped[List["Team"]] = relationship(
        "app.db.social.team.Team",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    team_season_aggregates: Mapped[list["TeamSeasonAggregate"]] = relationship(
        "TeamSeasonAggregate",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    team_event_aggregates: Mapped[list["TeamEventAggregate"]] = relationship(
        "TeamEventAggregate",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    powerup_targets_received: Mapped[list["PowerUpUseTarget"]] = relationship(
        "PowerUpUseTarget",
        foreign_keys="PowerUpUseTarget.target_group_id",
        back_populates="target_group",
    )

    powerup_uses: Mapped[list["PowerUpUse"]] = relationship(
        "PowerUpUse",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    powerup_assignments: Mapped[list["PowerUpAssignment"]] = relationship(
        "PowerUpAssignment",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="group",
    )
