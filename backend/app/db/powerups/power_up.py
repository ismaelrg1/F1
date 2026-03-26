from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Index,
    String,
    UniqueConstraint,
    CheckConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.powerups import PowerUpAssignment, PowerUpUse
    from app.db.powerups import PowerUpRestriction


from app.db.enums import PowerUpTargetMode

class PowerUp(Base):
    __tablename__ = "powerups"
    __table_args__ = (
        UniqueConstraint("code", name="uq_powerups_code"),
        Index("ix_powerups_is_enabled", "is_enabled"),
        CheckConstraint("length(code) >= 2", name="ck_powerups_code_minlen"),
        CheckConstraint("length(name) >= 2", name="ck_powerups_name_minlen"),
        {"schema": "powerups"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    target_mode: Mapped[PowerUpTargetMode] = mapped_column(
        Enum(PowerUpTargetMode, name="powerup_target_mode_enum", schema="powerups"),
        nullable=False,
        server_default=text("'SINGLE'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # --------------------
    # Relationships
    # --------------------

    # Reglas de habilitación/deshabilitación por contexto/sesión
    restrictions: Mapped[List["PowerUpRestriction"]] = relationship(
        "PowerUpRestriction",
        back_populates="powerup",
        cascade="all, delete-orphan",
    )

    # Inventario/cantidad por usuario-temporada (si lo usas)
    assignments: Mapped[List["PowerUpAssignment"]] = relationship(
        "PowerUpAssignment",
        back_populates="powerup",
        cascade="all, delete-orphan",
    )

    # Usos realizados del powerup
    uses: Mapped[List["PowerUpUse"]] = relationship(
        "PowerUpUse",
        back_populates="powerup",
        cascade="all, delete-orphan",
    )