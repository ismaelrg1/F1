from __future__ import annotations

from sqlalchemy import ForeignKey, DateTime, Index, func, CheckConstraint, text, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional
from datetime import datetime

if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.betting import BetContext
    from app.db.competition import EventSession, TestingEventSession
    from app.db.social import Group, Team

from app.db.base import Base

class BetEditPermission(Base):
    __tablename__ = "bet_edit_permissions"
    __table_args__ = (
        CheckConstraint(
            "starts_at < ends_at",
            name="ck_bet_edit_permissions_window_order",
        ),
        CheckConstraint(
            "max_modifications IS NULL OR max_modifications >= 1",
            name="ck_bet_edit_permissions_max_modifications_positive",
        ),
        CheckConstraint(
            "NOT (event_session_id IS NOT NULL AND testing_event_session_id IS NOT NULL)",
            name="ck_bet_edit_permissions_not_both_session_ids",
        ),
        CheckConstraint(
            "("
            "(applies_to_all = true AND group_id IS NULL AND user_id IS NULL AND team_id IS NULL) OR "
            "(applies_to_all = false AND (group_id IS NOT NULL OR user_id IS NOT NULL OR team_id IS NOT NULL))"
            ")",
            name="ck_bet_edit_permissions_target",
        ),
        Index(
            "ix_bet_edit_permissions_scope",
            "bet_context_id",
            "event_session_id",
            "testing_event_session_id",
        ),
        Index(
            "ix_bet_edit_permissions_window",
            "starts_at",
            "ends_at",
        ),
        {"schema": "betting"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    bet_context_id: Mapped[int] = mapped_column(
        ForeignKey("betting.bet_contexts.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.event_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )

    testing_event_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competition.testing_event_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )

    applies_to_all: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("social.groups.id", ondelete="CASCADE"),
        nullable=True,
    )

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=True,
    )

    team_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("social.teams.id", ondelete="CASCADE"),
        nullable=True,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    max_modifications: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("auth.users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    bet_context: Mapped["BetContext"] = relationship(
        "BetContext",
        back_populates="edit_permissions",
    )

    event_session: Mapped[Optional["EventSession"]] = relationship(
        "EventSession",
        back_populates="bet_edit_permissions",
    )

    testing_event_session: Mapped[Optional["TestingEventSession"]] = relationship(
        "TestingEventSession",
        back_populates="bet_edit_permissions",
    )

    group: Mapped[Optional["Group"]] = relationship(
        "Group",
        back_populates="bet_edit_permissions",
    )

    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="bet_edit_permissions",
    )

    team: Mapped[Optional["Team"]] = relationship(
        "Team",
        back_populates="bet_edit_permissions",
    )

    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="created_bet_edit_permissions",
    )