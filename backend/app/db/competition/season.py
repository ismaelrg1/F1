from __future__ import annotations
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, text, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import List, TYPE_CHECKING, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import RaceEvent, TestingEvent, SeasonDriver, SeasonTeam, SeasonEngine, DriverEntry
    from app.db.betting import BetTemplate, BetContext
    from app.db.scoring import ScoreSeasonAggregate, ScoringRule, TeamSeasonAggregate
    from app.db.powerups import PowerUpAssignment

class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1950 AND 2100", name="ck_seasons_year_range"),
        Index("ix_seasons_year", "year", unique=True),
        Index(
            "uq_seasons_single_active",
            "is_active",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
        CheckConstraint(
            "betting_open_at IS NULL OR lock_cutoff IS NULL OR betting_open_at < lock_cutoff",
            name="ck_seasons_betting_window_order",
        ),
        {"schema": "competition"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    betting_open_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    lock_cutoff: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    scheduled_lock_cutoff: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    race_events: Mapped[List["RaceEvent"]] = relationship(
        'RaceEvent',
        back_populates="season",
    )

    testing_events: Mapped[List["TestingEvent"]] = relationship(
        'TestingEvent',
        back_populates="season",
    )

    season_drivers: Mapped[List["SeasonDriver"]] = relationship(
        'SeasonDriver',
        back_populates="season",
        cascade="all, delete-orphan"
    )

    season_teams: Mapped[List["SeasonTeam"]] = relationship(
        'SeasonTeam',
        back_populates="season",
        cascade="all, delete-orphan"
    )

    season_engines: Mapped[List["SeasonEngine"]] = relationship(
        'SeasonEngine',
        back_populates="season",
        cascade="all, delete-orphan"
    )

    driver_entries: Mapped[List["DriverEntry"]] = relationship(
        'DriverEntry',
        back_populates="season",
    )

    bet_templates: Mapped[List["BetTemplate"]] = relationship(
        'BetTemplate',
        back_populates="season",
        cascade="all, delete-orphan",
    )

    bet_contexts: Mapped[List["BetContext"]] = relationship(
        'BetContext',
        back_populates="season",
    )

    score_season_aggregates: Mapped[List["ScoreSeasonAggregate"]] = relationship(
        'ScoreSeasonAggregate',
        back_populates="season",
        cascade="all, delete-orphan",
    )

    team_season_aggregates: Mapped[list["TeamSeasonAggregate"]] = relationship(
        "TeamSeasonAggregate",
        back_populates="season",
    )

    scoring_rules: Mapped[list["ScoringRule"]] = relationship(
        "ScoringRule",
        back_populates="season",
        cascade="all, delete-orphan",
    )

    powerup_assignments: Mapped[list["PowerUpAssignment"]] = relationship(
        "PowerUpAssignment",
        back_populates="season",
        cascade="all, delete-orphan",
    )
