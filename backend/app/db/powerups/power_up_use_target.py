from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Any

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    CheckConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.powerups import PowerUpUse
    from app.db.auth import User
    from app.db.social import Group, Team

from app.db.enums import PowerUpTargetType

class PowerUpUseTarget(Base):
    __tablename__ = "powerup_use_targets"
    __table_args__ = (
        # Lookups típicos
        Index("ix_put_powerup_use_id", "powerup_use_id"),
        Index("ix_put_target_type", "target_type"),
        Index("ix_put_target_user_id", "target_user_id"),
        Index("ix_put_target_team_id", "target_team_id"),
        Index("ix_put_target_group_id", "target_group_id"),
        Index(
            "uq_put_use_user",
            "powerup_use_id",
            "target_user_id",
            unique=True,
            postgresql_where=text("target_user_id IS NOT NULL"),
        ),
        Index(
            "uq_put_use_team",
            "powerup_use_id",
            "target_team_id",
            unique=True,
            postgresql_where=text("target_team_id IS NOT NULL"),
        ),
        Index(
            "uq_put_use_group",
            "powerup_use_id",
            "target_group_id",
            "target_type",
            unique=True,
            postgresql_where=text("target_group_id IS NOT NULL"),
        ),
        Index(
            "uq_put_use_all",
            "powerup_use_id",
            unique=True,
            postgresql_where=text("target_type = 'ALL'"),
        ),

        # Consistencia de target según target_type
        CheckConstraint(
            "("
            " (target_type = 'USER' AND target_user_id IS NOT NULL AND target_team_id IS NULL AND target_group_id IS NULL) OR "
            " (target_type = 'TEAM' AND target_team_id IS NOT NULL AND target_user_id IS NULL AND target_group_id IS NULL) OR "
            " (target_type = 'GROUP' AND target_group_id IS NOT NULL AND target_user_id IS NULL AND target_team_id IS NULL) OR "
            " (target_type = 'GROUP_EXCEPT_ACTOR' AND target_group_id IS NOT NULL AND target_user_id IS NULL AND target_team_id IS NULL) OR "
            " (target_type = 'ALL' AND target_user_id IS NULL AND target_team_id IS NULL AND target_group_id IS NULL) "
            ")",
            name="ck_put_target_type_matches_ids",
        ),

        {"schema": "powerups"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    powerup_use_id: Mapped[int] = mapped_column(
        ForeignKey("powerups.powerup_uses.id", ondelete="CASCADE"),
        nullable=False,
    )

    target_type: Mapped[PowerUpTargetType] = mapped_column(
        Enum(PowerUpTargetType, name="powerup_target_type_enum", schema="powerups"),
        nullable=False,
    )

    # Solo se usa si target_type == USER
    target_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Solo se usa si target_type == TEAM
    target_team_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("social.teams.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Solo se usa si target_type in (GROUP, GROUP_EXCEPT_ACTOR)
    target_group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Reglas extra opcionales (filtros, condiciones, etc.)
    rule_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # --------------------
    # Relationships
    # --------------------
    powerup_use: Mapped["PowerUpUse"] = relationship(
        "PowerUpUse",
        back_populates="targets",
    )

    target_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[target_user_id],
        back_populates="powerup_targets_received",
    )

    target_team: Mapped[Optional["Team"]] = relationship(
        "app.db.social.team.Team",
        foreign_keys=[target_team_id],
        back_populates="powerup_targets_received",
    )

    target_group: Mapped[Optional["Group"]] = relationship(
        "Group",
        foreign_keys=[target_group_id],
        back_populates="powerup_targets_received",
    )
