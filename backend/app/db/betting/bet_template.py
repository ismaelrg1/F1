from __future__ import annotations

from sqlalchemy import Enum,  ForeignKey, Index, text, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional, List

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import Season
    from app.db.betting import BetTemplateItem


from app.db.enums import BetContextKind, SessionType, BetTemplateScope


class BetTemplate(Base):
    __tablename__ = "bet_templates"
    __table_args__ = (
        # Reglas coherencia:
        # - Si NO es GP: scope debe ser EVENT y session_type NULL
        # - Si es GP:
        #    - scope EVENT => session_type NULL
        #    - scope SESSION => session_type NOT NULL
        CheckConstraint(
            "("
            "  (scope = 'EVENT' AND session_type IS NULL)"
            "  OR"
            "  (scope = 'SESSION' AND context_kind = 'GP' AND session_type IS NOT NULL)"
            ")",
            name="ck_bet_templates_scope_sessiontype",
        ),

        # Unicidad: GP por sesión
        Index(
            "uq_bet_templates_gp_session",
            "season_id",
            "context_kind",
            "scope",
            "session_type",
            unique=True,
            postgresql_where=text("context_kind = 'GP' AND scope = 'SESSION'"),
        ),

        # Unicidad: GP entero
        Index(
            "uq_bet_templates_gp_event",
            "season_id",
            "context_kind",
            "scope",
            unique=True,
            postgresql_where=text("context_kind = 'GP' AND scope = 'EVENT'"),
        ),

        # Unicidad: PRETESTING / SEASON
        Index(
            "uq_bet_templates_non_gp",
            "season_id",
            "context_kind",
            unique=True,
            postgresql_where=text("context_kind <> 'GP'"),
        ),

        Index("ix_bet_templates_season_kind", "season_id", "context_kind"),
        {"schema": "betting"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    season_id: Mapped[int] = mapped_column(
        ForeignKey("competition.seasons.id", ondelete="RESTRICT"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    context_kind: Mapped[BetContextKind] = mapped_column(
        Enum(BetContextKind, name="bet_context_kind_enum", schema="betting"),
        nullable=False,
    )

    scope: Mapped[BetTemplateScope] = mapped_column(
        Enum(BetTemplateScope, name="bet_template_scope_enum", schema="betting"),
        nullable=False,
        server_default=text("'EVENT'"),
    )

    session_type: Mapped[Optional[SessionType]] = mapped_column(
        Enum(
            SessionType, 
            name="event_session_type_enum", 
            schema="competition", 
            create_type=False),
        nullable=True,
    )

    season: Mapped["Season"] = relationship(
        'Season', 
        back_populates="bet_templates"
    )

    items: Mapped[List["BetTemplateItem"]] = relationship(
        "BetTemplateItem",
        back_populates="bet_template",
        cascade="all, delete-orphan",
    )