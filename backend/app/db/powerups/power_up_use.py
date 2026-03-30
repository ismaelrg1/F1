from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING, Dict, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.betting import BetContext
    from app.db.competition import EventSession
    from app.db.powerups import PowerUp
    from app.db.powerups import PowerUpUseTarget
    from app.db.social import Group


class PowerUpUse(Base):
    __tablename__ = "powerup_uses"
    __table_args__ = (
        Index(
            "uq_powerup_uses_user_context_powerup",
            "user_id",
            "group_id",
            "bet_context_id",
            "powerup_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL"),
        ),
        Index(
            "uq_powerup_uses_user_session_powerup",
            "user_id",
            "group_id",
            "bet_context_id",
            "event_session_id",
            "powerup_id",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL"),
        ),
        # Lookups importantes
        Index("ix_powerup_uses_user_id", "user_id"),
        Index("ix_powerup_uses_group_id", "group_id"),
        Index("ix_powerup_uses_bet_context_id", "bet_context_id"),
        Index("ix_powerup_uses_event_session_id", "event_session_id"),
        Index("ix_powerup_uses_powerup_id", "powerup_id"),
        Index("ix_powerup_uses_group_user", "group_id", "user_id"),
        Index("ix_powerup_uses_context_powerup", "bet_context_id", "powerup_id"),
        CheckConstraint(
            "event_session_id IS NULL OR bet_context_id IS NOT NULL",
            name="ck_powerup_uses_session_requires_context",
        ),

        {"schema": "powerups"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Usuario que usa el powerup
    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Grupo en el que se usa (muy recomendado)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Contexto del evento (GP, Testing, Season)
    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Opcional: sesión concreta
    event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Tipo de powerup
    powerup_id: Mapped[int] = mapped_column(
        ForeignKey("powerups.powerups.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Cuándo se usó
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Reglas dinámicas opcionales
    rule_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # --------------------
    # Relationships
    # --------------------

    user: Mapped["User"] = relationship(
        "User",
        back_populates="powerup_uses",  
    )

    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="powerup_uses",
    )

    bet_context: Mapped["BetContext"] = relationship(
        "BetContext",
        back_populates="powerup_uses",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        "EventSession",
        back_populates="powerup_uses",
    )

    powerup: Mapped["PowerUp"] = relationship(
        "PowerUp",
        back_populates="uses",
    )

    targets: Mapped[list["PowerUpUseTarget"]] = relationship(
        "PowerUpUseTarget",
        back_populates="powerup_use",
        cascade="all, delete-orphan",
    )
