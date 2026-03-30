from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    CheckConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.betting import BetContext
    from app.db.competition import Season
    from app.db.powerups import PowerUp
    from app.db.social import Group


class PowerUpAssignment(Base):
    __tablename__ = "powerup_assignments"
    __table_args__ = (
        # ---------------------------------------------------------
        # 1) EXACTAMENTE UNA de: season_id o bet_context_id
        # ---------------------------------------------------------
        CheckConstraint(
            "("
            "(season_id IS NOT NULL AND bet_context_id IS NULL) OR "
            "(season_id IS NULL AND bet_context_id IS NOT NULL)"
            ")",
            name="ck_powerup_assignments_scope_xor",
        ),

        # ---------------------------------------------------------
        # 2) Unicidades (parciales)
        #   - Temporada: (group, user, season, powerup) si bet_context_id IS NULL
        #   - Evento:    (group, user, bet_context, powerup) si bet_context_id IS NOT NULL
        # ---------------------------------------------------------
        Index(
            "uq_powerup_assignments_season",
            "group_id", "user_id", "season_id", "powerup_id",
            unique=True,
            postgresql_where=text("bet_context_id IS NULL"),
        ),
        Index(
            "uq_powerup_assignments_event",
            "group_id", "user_id", "bet_context_id", "powerup_id",
            unique=True,
            postgresql_where=text("bet_context_id IS NOT NULL"),
        ),

        # ---------------------------------------------------------
        # 3) Checks
        # ---------------------------------------------------------
        CheckConstraint("quantity >= 0", name="ck_powerup_assignments_quantity_nonneg"),

        # ---------------------------------------------------------
        # 4) Lookups típicos
        # ---------------------------------------------------------
        Index("ix_powerup_assignments_group_id", "group_id"),
        Index("ix_powerup_assignments_user_id", "user_id"),
        Index("ix_powerup_assignments_season_id", "season_id"),
        Index("ix_powerup_assignments_bet_context_id", "bet_context_id"),
        Index("ix_powerup_assignments_powerup_id", "powerup_id"),
        Index("ix_powerup_assignments_group_user", "group_id", "user_id"),

        {"schema": "powerups"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    season_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="CASCADE"),
        nullable=True,
    )

    bet_context_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="CASCADE"),
        nullable=True,
    )

    powerup_id: Mapped[int] = mapped_column(
        ForeignKey("powerups.powerups.id", ondelete="RESTRICT"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    # útil para auditoría rápida (además de tu audit_logs)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # si quieres “desactivar” asignaciones sin borrarlas (opcional)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    # --------------------
    # Relationships
    # --------------------

    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="powerup_assignments",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="powerup_assignments",
    )

    season: Mapped["Season"] = relationship(
        "Season",
        back_populates="powerup_assignments",
    )

    bet_context: Mapped[Optional["BetContext"]] = relationship(
        "BetContext",
        back_populates="powerup_assignments",
    )

    powerup: Mapped["PowerUp"] = relationship(
        "PowerUp",
        back_populates="assignments",
    )