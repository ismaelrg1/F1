from __future__ import annotations

from sqlalchemy import ForeignKey, DateTime, String, CheckConstraint, Index, text, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ExcludeConstraint

from typing import TYPE_CHECKING, Optional
from datetime import datetime

if TYPE_CHECKING:
    from app.db.competition import Driver, TeamF1, Engine, RaceEvent, Season, EventSession

from app.db.base import Base

class DriverEntry(Base):
    """
    Reglas:
    - season_id, team_id, seat_index definen el "asiento" (1 o 2) dentro del equipo en una temporada.
    - Hierarquía (prioridad al resolver roster):
        1) event_session_id (override por sesión)
        2) race_event_id (override por GP)
        3) season-level (race_event_id NULL, event_session_id NULL) usando ventana active_from/active_to
    - active_from/active_to permiten "cambios desde X hasta Y".
      Si ambas NULL => válido "siempre" (ojo: entonces no puedes tener más de uno solapando).
    """

    __tablename__ = "driver_entries"
    __table_args__ = (
        CheckConstraint("seat_index IN (1, 2)", name="ck_driver_entries_seat_index_1_2"),
        CheckConstraint(
            "(active_from IS NULL OR active_to IS NULL OR active_from < active_to)",
            name="ck_driver_entries_active_window_order",
        ),

        CheckConstraint(
            "NOT (race_event_id IS NOT NULL AND event_session_id IS NOT NULL)",
            name="ck_driver_entries_not_both_event_and_session",
        ),

        # Evita solapes de tiempo PARA:
        # - season-level roster (race_event_id IS NULL AND event_session_id IS NULL)
        #
        # Usa un rango tstzrange con:
        #   [active_from, active_to)
        # Si active_from es NULL => -infinito
        # Si active_to   es NULL => +infinito
        ExcludeConstraint(
            ("season_id", "="),
            ("team_id", "="),
            ("seat_index", "="),
            (
                text("tstzrange(active_from, active_to, '[)')"),
                "&&",
            ),
            name="excl_driver_entries_season_team_seat_time_overlap",
            using="gist",
            where=text("race_event_id IS NULL AND event_session_id IS NULL"),
        ),

        # Evita duplicados exactos por GP (no hace falta excluir por tiempo, porque GP es discreto)
        Index(
            "uq_driver_entries_gp_season_event_team_seat",
            "season_id",
            "race_event_id",
            "team_id",
            "seat_index",
            unique=True,
            postgresql_where=text("race_event_id IS NOT NULL AND event_session_id IS NULL"),
        ),

        # Evita duplicados exactos por Sesión (máximo 1 override por sesión para ese asiento)
        Index(
            "uq_driver_entries_session_season_session_team_seat",
            "season_id",
            "event_session_id",
            "team_id",
            "seat_index",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL"),
        ),

        Index("ix_driver_entries_season_team_seat", "season_id", "team_id", "seat_index"),
        Index("ix_driver_entries_season_level_window", "season_id", "team_id", "seat_index", "active_from", "active_to"),

        {"schema": "competition"},
    )


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="RESTRICT"),
        nullable=False,
        )
    
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("competition.drivers.id", ondelete="RESTRICT"),
        nullable=False,
        )
    
    team_id: Mapped[int] = mapped_column(
        ForeignKey("competition.teams.id", ondelete="RESTRICT"),
        nullable=False,
        )
    
    engine_id: Mapped[int] = mapped_column(
        ForeignKey("competition.engines.id", ondelete="RESTRICT"),
        nullable=False,
        )
    
    # 1 o 2 dentro del equipo
    seat_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    
    active_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    active_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # NULL => season-level roster (por ventanas)
    race_event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.race_events.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # NULL => no es override de sesión
    event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="RESTRICT"),
        nullable=True,
    )


    season: Mapped["Season"] = relationship(
        'Season',
        back_populates="driver_entries"
    )

    driver: Mapped["Driver"] = relationship(
        'Driver',
        back_populates="driver_entries"
    )

    team: Mapped["TeamF1"] = relationship(
        "app.db.competition.team.TeamF1",
        back_populates="driver_entries"
    )

    engine: Mapped["Engine"] = relationship(
        'Engine',
        back_populates="driver_entries"
    )

    race_event: Mapped[Optional["RaceEvent"]] = relationship(
        'RaceEvent',
        back_populates="driver_entries"
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        'EventSession',
        back_populates="driver_entries"
    )
