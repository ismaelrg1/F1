from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, String, func, text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.audit import AuditLog
    from app.db.auth import Role, PasswordResetToken
    from app.db.betting import Bet, BetPick, BetEditPermission
    from app.db.powerups import PowerUpAssignment, PowerUpUse, PowerUpUseTarget
    from app.db.scoring import ResultPublication, Score, ScoreSeasonAggregate, ScoreSession
    from app.db.social import GroupMembership, TeamMembership


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(username) >= 3", name="ck_users_username_minlen"),
        CheckConstraint("length(email) >= 5", name="ck_users_email_minlen"),
        Index("ix_users_created_at", "created_at"),
        Index("ix_users_auth_provider", "auth_provider"),
        Index("ix_users_google_sub", "google_sub"),
        Index("ix_users_public_id", "public_id"),
        {"schema": "auth"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid4,
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    auth_provider: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'LOCAL'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="auth.user_roles",
        back_populates="users",
    )

    bets: Mapped[List["Bet"]] = relationship(
        "Bet",
        back_populates="user",
    )

    bet_picks_invalidated: Mapped[List["BetPick"]] = relationship(
        "BetPick",
        foreign_keys="BetPick.invalidated_by_user_id",
        back_populates="invalidated_by",
    )

    scores: Mapped[List["Score"]] = relationship(
        "Score",
        back_populates="user",
    )

    score_sessions: Mapped[List["ScoreSession"]] = relationship(
        "ScoreSession",
        back_populates="user",
    )

    result_publications_published: Mapped[List["ResultPublication"]] = relationship(
        "ResultPublication",
        foreign_keys="ResultPublication.published_by_user_id",
        back_populates="published_by",
    )

    score_season_aggregates: Mapped[List["ScoreSeasonAggregate"]] = relationship(
        "ScoreSeasonAggregate",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    group_memberships: Mapped[List["GroupMembership"]] = relationship(
        "GroupMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    team_memberships: Mapped[List["TeamMembership"]] = relationship(
        "TeamMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    powerup_targets_received: Mapped[list["PowerUpUseTarget"]] = relationship(
        "PowerUpUseTarget",
        foreign_keys="PowerUpUseTarget.target_user_id",
        back_populates="target_user",
    )

    powerup_uses: Mapped[list["PowerUpUse"]] = relationship(
        "PowerUpUse",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    powerup_assignments: Mapped[list["PowerUpAssignment"]] = relationship(
        "PowerUpAssignment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    audit_logs_as_actor: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        foreign_keys="AuditLog.actor_user_id",
        back_populates="actor_user",
    )

    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    bet_edit_permissions: Mapped[list["BetEditPermission"]] = relationship(
        "BetEditPermission",
        foreign_keys="BetEditPermission.user_id",
        back_populates="user",
    )

    created_bet_edit_permissions: Mapped[list["BetEditPermission"]] = relationship(
        "BetEditPermission",
        foreign_keys="BetEditPermission.created_by_user_id",
        back_populates="created_by_user",
    )
