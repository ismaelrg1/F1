from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.competition import Driver, Season, SeasonDriver
from app.db.enums import SeasonDriverStatus
from app.domain.admin.drivers.models import (
    AdminDriver,
    AdminDriverSeason,
    AdminSeasonDriver,
)
from app.domain.admin.drivers.ports import AdminDriverRepository


class SqlAlchemyAdminDriverRepository(AdminDriverRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_code(self, code: str) -> AdminDriver | None:
        stmt = select(Driver).where(Driver.code == code)
        driver = self._session.execute(stmt).scalar_one_or_none()
        if driver is None:
            return None
        return AdminDriver(
            id=driver.id,
            code=driver.code,
            name=driver.name,
        )

    def create(self, *, code: str, name: str) -> AdminDriver:
        driver = Driver(code=code, name=name)
        self._session.add(driver)
        self._session.flush()
        self._session.refresh(driver)
        return AdminDriver(
            id=driver.id,
            code=driver.code,
            name=driver.name,
        )

    def get_season_by_year(self, year: int) -> AdminDriverSeason | None:
        stmt = select(Season).where(Season.year == year)
        season = self._session.execute(stmt).scalar_one_or_none()
        if season is None:
            return None
        return AdminDriverSeason(
            id=season.id,
            year=season.year,
        )

    def get_season_driver(self, *, season_id: int, driver_id: int) -> AdminSeasonDriver | None:
        stmt = (
            select(SeasonDriver)
            .where(
                SeasonDriver.season_id == season_id,
                SeasonDriver.driver_id == driver_id,
            )
            .options(
                joinedload(SeasonDriver.season),
                joinedload(SeasonDriver.driver),
            )
        )
        season_driver = self._session.execute(stmt).scalar_one_or_none()
        if season_driver is None:
            return None
        return self._map_season_driver(season_driver)

    def create_season_driver(
        self,
        *,
        season_id: int,
        driver_id: int,
        status: str,
    ) -> AdminSeasonDriver:
        season_driver = SeasonDriver(
            season_id=season_id,
            driver_id=driver_id,
            status=SeasonDriverStatus(status),
        )
        self._session.add(season_driver)
        self._session.flush()

        stmt = (
            select(SeasonDriver)
            .where(
                SeasonDriver.season_id == season_driver.season_id,
                SeasonDriver.driver_id == season_driver.driver_id,
            )
            .options(
                joinedload(SeasonDriver.season),
                joinedload(SeasonDriver.driver),
            )
        )
        created = self._session.execute(stmt).scalar_one()
        return self._map_season_driver(created)

    @staticmethod
    def _map_season_driver(season_driver: SeasonDriver) -> AdminSeasonDriver:
        return AdminSeasonDriver(
            season_year=season_driver.season.year,
            driver_code=season_driver.driver.code,
            status=season_driver.status.value,
        )
