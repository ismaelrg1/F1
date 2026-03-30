from __future__ import annotations

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import List, TYPE_CHECKING, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.competition import Circuit

class Country(Base):
    __tablename__ = "countries"
    __table_args__ = (
        CheckConstraint(
            "iso2 ~ '^[A-Z]{2}$'",
            name="ck_country_iso2_format"
        ),
        CheckConstraint(
            "length(name) >= 2",
            name="ck_countries_name_minlen",
        ),
        {"schema": "competition"}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    iso2: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    flag_asset_url: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


    circuits: Mapped[List["Circuit"]] = relationship(
        'Circuit',
        back_populates="country",
    )
