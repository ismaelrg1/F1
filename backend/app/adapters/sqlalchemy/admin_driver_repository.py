from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Driver, Season, SeasonDriver
from app.domain.admin.drivers.ports import AdminDriverRepository


class SqlAlchemyAdminDriverRepository(AdminDriverRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_code(self, code: str) -> Driver | None:
        stmt = select(Driver).where(Driver.code == code)
        return self._session.execute(stmt).scalar_one_or_none()

    def create(self, *, code: str, name: str) -> Driver:
        driver = Driver(code=code, name=name)
        self._session.add(driver)
        self._session.flush()
        self._session.refresh(driver)
        return driver

    def get_season_by_year(self, year: int) -> Season | None:
        stmt = select(Season).where(Season.year == year)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_season_driver(self, *, season_id: int, driver_id: int) -> SeasonDriver | None:
        stmt = select(SeasonDriver).where(
            SeasonDriver.season_id == season_id,
            SeasonDriver.driver_id == driver_id,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def create_season_driver(self, *, season_id: int, driver_id: int, status) -> SeasonDriver:
        season_driver = SeasonDriver(
            season_id=season_id,
            driver_id=driver_id,
            status=status,
        )
        self._session.add(season_driver)
        self._session.flush()
        self._session.refresh(season_driver)
        return season_driver