from fastapi import APIRouter

from . import (
    circuits,
    countries,
    drivers,
    engines,
    fastf1,
    race_events,
    seasons,
    teams,
    testing_events,
)

router = APIRouter()
router.include_router(seasons.router)
router.include_router(countries.router)
router.include_router(circuits.router)
router.include_router(fastf1.router)
router.include_router(testing_events.router)
router.include_router(race_events.router)
router.include_router(drivers.router)
router.include_router(teams.router)
router.include_router(engines.router)

__all__ = ["router"]