from __future__ import annotations

from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import List, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import SeasonEngine, DriverEntry

class Engine(Base):
    __tablename__ = "engines"
    __table_args__ = (
        CheckConstraint(
            "code ~ '^[A-Z]{2,10}$'",
            name="ck_engine_code_format"
        ),
        CheckConstraint(
            "length(name) >= 2",
            name="ck_engines_name_minlen",
        ),
        {"schema": "competition"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    season_engines: Mapped[List["SeasonEngine"]] = relationship(
        'SeasonEngine',
        back_populates="engine",
    )

    driver_entries: Mapped[List["DriverEntry"]] = relationship(
        'DriverEntry',
        back_populates="engine",
    )
