from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Index, Enum, String, CheckConstraint, ForeignKey, Boolean, text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional, List

from app.db.base import Base

from app.db.enums import BetContextKind

if TYPE_CHECKING:
    from app.db.betting import Bet, BetException
    from app.db.competition import Season, RaceEvent, TestingEvent
    from app.db.scoring import Score, ScoreSession, OfficialResult, ResultPublication, ScoringRule, TeamEventAggregate
    from app.db.social import Group
    from app.db.powerups import PowerUpUse, PowerUpRestriction, PowerUpAssignment


class BetContext(Base):
    __tablename__ = "bet_contexts"
    __table_args__ = (
        # checks (los tuyos se quedan igual)
        CheckConstraint(
            "NOT (race_event_id IS NOT NULL AND testing_event_id IS NOT NULL)",
            name="ck_bet_contexts_not_both_event_ids",
        ),
        CheckConstraint(
            "("
            " (kind = 'GP' AND race_event_id IS NOT NULL AND testing_event_id IS NULL) OR "
            " (kind = 'PRETESTING' AND testing_event_id IS NOT NULL AND race_event_id IS NULL) OR "
            " (kind = 'SEASON' AND race_event_id IS NULL AND testing_event_id IS NULL)"
            ")",
            name="ck_bet_contexts_kind_matches_ids",
        ),
        CheckConstraint(
            "results_published = false OR results_published_at IS NOT NULL",
            name="ck_bet_contexts_published_requires_timestamp",
        ),
        CheckConstraint(
            "results_published = true OR results_published_at IS NULL",
            name="ck_bet_contexts_unpublished_has_no_timestamp",
        ),
        CheckConstraint(
            "length(label) >= 2",
            name="ck_bet_contexts_label_minlen",
        ),

        # ✅ SEASON: 1 por (group, season)
        Index(
            "uq_bet_contexts_group_season",
            "group_id", "season_id",
            unique=True,
            postgresql_where=text(
                "kind = 'SEASON' AND race_event_id IS NULL AND testing_event_id IS NULL"
            ),
        ),

        # ✅ GP: 1 por (group, race_event)
        Index(
            "uq_bet_contexts_group_race_event",
            "group_id", "race_event_id",
            unique=True,
            postgresql_where=text(
                "kind = 'GP' AND race_event_id IS NOT NULL AND testing_event_id IS NULL"
            ),
        ),

        # ✅ PRETESTING: 1 por (group, testing_event)
        Index(
            "uq_bet_contexts_group_testing_event",
            "group_id", "testing_event_id",
            unique=True,
            postgresql_where=text(
                "kind = 'PRETESTING' AND testing_event_id IS NOT NULL AND race_event_id IS NULL"
            ),
        ),

        # índices de listado/lookup
        Index("ix_bet_contexts_group_season_kind", "group_id", "season_id", "kind"),
        Index("ix_bet_contexts_group_id", "group_id"),
        Index("ix_bet_contexts_season_id", "season_id"),
        Index("ix_bet_contexts_race_event_id", "race_event_id"),
        Index("ix_bet_contexts_testing_event_id", "testing_event_id"),
        Index("ix_bet_contexts_kind", "kind"),
        Index("ix_bet_contexts_public_id", "public_id"),

        {"schema": "betting"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid4,
    )

    kind: Mapped[BetContextKind] = mapped_column(
        Enum(BetContextKind, name="bet_context_kind_enum", schema="betting", create_type=False),
        nullable=False,
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Exactly one of:
    # - race_event_id (GP)
    # - testing_event_id (PRETESTING)
    # - none (SEASON)
    race_event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.race_events.id", ondelete="RESTRICT"),
        nullable=True,
    )

    testing_event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.testing_events.id", ondelete="RESTRICT"),
        nullable=True,
    )

    label: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    results_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    results_published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="bet_contexts",
    )


    season: Mapped["Season"] = relationship(
        'Season',
        back_populates="bet_contexts",
    )

    race_event: Mapped[Optional["RaceEvent"]] = relationship(
        'RaceEvent',
        back_populates="bet_context",
    )

    testing_event: Mapped[Optional["TestingEvent"]] = relationship(
        'TestingEvent',
        back_populates="bet_context",
    )

    bet_exceptions: Mapped[List["BetException"]] = relationship(
        'BetException',
        back_populates="bet_context",
    )

    bets: Mapped[List["Bet"]] = relationship(
        "Bet",
        back_populates="bet_context",
        cascade="all, delete-orphan",
    )

    scores: Mapped[List["Score"]] = relationship(
        'Score',
        back_populates="bet_context",
    )

    score_sessions: Mapped[List["ScoreSession"]] = relationship(
        'ScoreSession',
        back_populates="bet_context",
    )

    scoring_rules: Mapped[list["ScoringRule"]] = relationship(
        "ScoringRule",
        back_populates="bet_context",
        cascade="all, delete-orphan",
    )

    official_results: Mapped[List["OfficialResult"]] = relationship(
        'OfficialResult',
        back_populates="bet_context",
        cascade="all, delete-orphan",
    )

    result_publications: Mapped[List["ResultPublication"]] = relationship(
        'ResultPublication',
        back_populates="bet_context",
        cascade="all, delete-orphan",
    )

    team_event_aggregates: Mapped[list["TeamEventAggregate"]] = relationship(
        "TeamEventAggregate",
        back_populates="bet_context",
        cascade="all, delete-orphan",
    )

    powerup_uses: Mapped[list["PowerUpUse"]] = relationship(
        "PowerUpUse",
        back_populates="bet_context",
        cascade="all, delete-orphan",
    )

    powerup_restrictions: Mapped[list["PowerUpRestriction"]] = relationship(
        "PowerUpRestriction",
        back_populates="bet_context",
        cascade="all, delete-orphan",
    )

    powerup_assignments: Mapped[list["PowerUpAssignment"]] = relationship(
        "PowerUpAssignment",
        back_populates="bet_context",
        cascade="all, delete-orphan",
    )

