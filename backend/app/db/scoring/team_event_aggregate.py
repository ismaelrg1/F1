from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    Numeric,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.social import Team, Group
    from app.db.betting import BetContext


class TeamEventAggregate(Base):
    __tablename__ = "team_event_aggregates"
    __table_args__ = (
        # 1 fila por (group, team, bet_context)
        Index(
            "uq_team_event_agg_group_team_ctx",
            "group_id", "team_id", "bet_context_id",
            unique=True,
        ),

        # ranking por evento (global/grupo)
        Index(
            "ix_team_event_agg_rank",
            "group_id", "bet_context_id", "total_points", "computed_at",
        ),

        # lookups típicos
        Index("ix_team_event_agg_team_id", "team_id"),
        Index("ix_team_event_agg_ctx_id", "bet_context_id"),
        Index("ix_team_event_agg_group_id", "group_id"),
        Index("ix_team_event_agg_group_team", "group_id", "team_id"),

        CheckConstraint(
            "total_points >= 0",
            name="ck_team_event_agg_total_points_nonneg",
        ),

        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("social.teams.id", ondelete="CASCADE"),
        nullable=False,
    )

    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="CASCADE"),
        nullable=False,
    )

    total_points: Mapped[Decimal] = mapped_column(
        Numeric(14, 8),
        nullable=False,
        server_default=text("0"),
    )

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # relationships
    group: Mapped["Group"] = relationship(
        "app.db.social.group.Group",
        back_populates="team_event_aggregates",
    )

    team: Mapped["Team"] = relationship(
        "app.db.social.team.Team",
        back_populates="team_event_aggregates",
    )

    bet_context: Mapped["BetContext"] = relationship(
        "app.db.betting.bet_context.BetContext",
        back_populates="team_event_aggregates",
    )
