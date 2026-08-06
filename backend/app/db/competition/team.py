from __future__ import annotations

from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import List, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import SeasonTeam, DriverEntry

class TeamF1(Base):
    __tablename__ = "teams"
    __table_args__ = (
        CheckConstraint(
            "code ~ '^[A-Z]{3}$'",
            name="ck_driver_code_format"
        ),
        CheckConstraint(
            "color ~ '^#[0-9A-Fa-f]{6}$'",
            name="ck_teams_color_format",
        ),
        {"schema": "competition"}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(3), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)

    season_teams: Mapped[List["SeasonTeam"]] = relationship(
        "SeasonTeam",
        back_populates="team",
    )

    driver_entries: Mapped[List["DriverEntry"]] = relationship(
        "DriverEntry",
        back_populates="team",
    )
