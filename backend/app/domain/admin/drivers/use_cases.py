from app.domain.admin.drivers.errors import (
    DriverAlreadyExistsError,
    DriverNotFoundForSeasonDriverError,
    SeasonDriverAlreadyExistsError,
    SeasonNotFoundForSeasonDriverError,
)
from app.domain.admin.drivers.ports import AdminDriverRepository


class CreateDriver:
    def __init__(self, repository: AdminDriverRepository):
        self._repository = repository

    def execute(self, *, code: str, name: str):
        normalized_code = code.strip().upper()

        existing = self._repository.get_by_code(normalized_code)
        if existing is not None:
            raise DriverAlreadyExistsError(code=normalized_code)

        return self._repository.create(
            code=normalized_code,
            name=name.strip(),
        )


class CreateSeasonDriver:
    def __init__(self, repository: AdminDriverRepository):
        self._repository = repository

    def execute(self, *, season_year: int, driver_code: str, status: str):
        season = self._repository.get_season_by_year(season_year)
        if season is None:
            raise SeasonNotFoundForSeasonDriverError(season_year=season_year)

        normalized_driver_code = driver_code.strip().upper()
        driver = self._repository.get_by_code(normalized_driver_code)
        if driver is None:
            raise DriverNotFoundForSeasonDriverError(driver_code=normalized_driver_code)

        existing = self._repository.get_season_driver(
            season_id=season.id,
            driver_id=driver.id,
        )
        if existing is not None:
            raise SeasonDriverAlreadyExistsError(
                season_year=season.year,
                driver_code=normalized_driver_code,
            )

        return self._repository.create_season_driver(
            season_id=season.id,
            driver_id=driver.id,
            status=status,
        )