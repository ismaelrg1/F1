from __future__ import annotations

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import List, TYPE_CHECKING, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import RaceEvent, TestingEvent, Country

class Circuit(Base):
    __tablename__ = "circuits"
    __table_args__ = {"schema": "competition"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    code: Mapped[str] = mapped_column(String(50), nullable=False)

    country_id: Mapped[int] = mapped_column(
        ForeignKey("competition.countries.id", ondelete="RESTRICT"),
        nullable=False)
    
    map_asset_url: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    image_asset_url: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


    race_events: Mapped[List["RaceEvent"]] = relationship(
        'RaceEvent',
        back_populates="circuit",
    )

    testing_events: Mapped[List["TestingEvent"]] = relationship(
        'TestingEvent',
        back_populates="circuit",
    )

    country: Mapped["Country"] = relationship(
        'Country',
        back_populates="circuits"
    )