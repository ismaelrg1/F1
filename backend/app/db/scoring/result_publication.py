from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, Text, ForeignKey, DateTime, Index, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship


from typing import TYPE_CHECKING, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import EventSession
    from app.db.betting import BetContext
    from app.db.auth import User


class ResultPublication(Base):
    __tablename__ = "result_publications"
    __table_args__ = (
        # 1) Solo 1 publicación por (contexto) cuando NO es por sesión
        Index(
            "uq_result_publications_ctx_nosession",
            "bet_context_id",
            unique=True,
            postgresql_where=text("event_session_id IS NULL"),
        ),

        # 2) Solo 1 publicación por (contexto + sesión) cuando SÍ es por sesión
        Index(
            "uq_result_publications_ctx_session",
            "bet_context_id",
            "event_session_id",
            unique=True,
            postgresql_where=text("event_session_id IS NOT NULL"),
        ),

        # 3) Índices típicos de lookup
        Index("ix_result_publications_ctx", "bet_context_id"),
        Index("ix_result_publications_session", "event_session_id"),
        Index("ix_result_publications_published_by", "published_by_user_id"),
        Index("ix_result_publications_published_at", "published_at"),

        # 4) Checks útiles
        CheckConstraint(
            "note IS NULL OR length(note) <= 5000",
            name="ck_result_publications_note_len",
        ),

        {"schema": "scoring"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # NULL => publicación para el evento completo (no una sesión concreta)
    event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # ondelete=SET NULL => nullable tiene que ser True
    published_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("auth.users.id", ondelete="SET NULL"),
        nullable=True,
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )


    bet_context: Mapped["BetContext"] = relationship(
        'BetContext',
        back_populates="result_publications",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        'EventSession',
        back_populates="result_publications",
    )

    published_by: Mapped[Optional["User"]] = relationship(
        'User',
        foreign_keys=[published_by_user_id],
        back_populates="result_publications_published",
    )

