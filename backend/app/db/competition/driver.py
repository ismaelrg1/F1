from __future__ import annotations

from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import List, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import SeasonDriver, DriverEntry

class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = (
        CheckConstraint(
            "code ~ '^[A-Z]{3}$'",
            name="ck_driver_code_format"
        ),   
        {"schema": "competition"}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(3), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    season_drivers: Mapped[List["SeasonDriver"]] = relationship(
        'SeasonDriver',
        back_populates="driver",
    )

    driver_entries: Mapped[List["DriverEntry"]] = relationship(
        'DriverEntry',
        back_populates="driver",
    )